# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_years, date_diff, getdate

OPEN_RENEWAL_STATUSES = ("Not Started", "Contacted", "Proposal Sent", "Negotiating")
RENEWAL_TERMINAL_STATUSES = ("Renewed", "Upgraded", "Not Renewing")

# Agreement Review flags an agreement that exceeded its allowance in this many closed months.
OVER_ALLOWANCE_MONTHS_THRESHOLD = 3
RENEWAL_LEAD_DAYS = 90

def month_of(date) -> str:
	#YYYY-MM
	return getdate(date).strftime("%Y-%m") if date else ""


def term_months(start_date, end_date) -> int:
	# Approximate number of months in a term (365 days -> 12)."""
	return max(1, round((date_diff(end_date, start_date) + 1) / 30.4375))


def agreement_year_start(start_date, as_of):
	#  Start of the agreement year for visit cap
	start, as_of = getdate(start_date), getdate(as_of)
	years = 0
	while add_years(start, years + 1) <= as_of:
		years += 1
	return add_years(start, years)


def validate_site_matches_agreement(doc):
	# Customer
	if not (doc.get("site") and doc.get("agreement")):
		return
	customer = frappe.db.get_value("Service Agreement", doc.agreement, "customer")
	site_customer = frappe.db.get_value("Site", doc.site, "customer")
	if customer and site_customer and customer != site_customer:
		frappe.throw(
			_("Site {0} belongs to {1}, not agreement {2}'s customer {3}.").format(
				frappe.bold(doc.site), site_customer, doc.agreement, customer
			),
			title=_("Customer Mismatch"),
		)


def timesheet_validate(doc, method=None):
	# Timesheet hook: month label, and defaults from Activity Type for newly added rows
	before = doc.get_doc_before_save()
	existing = {row.name for row in before.get("time_logs")} if before else set()

	for row in doc.get("time_logs"):
		if row.get("from_time"):
			row.custom_allowance_month = month_of(row.from_time)

		if row.name in existing or not row.get("activity_type"):
			continue

		flags = frappe.db.get_value(
			"Activity Type",
			row.activity_type,
			["custom_counts_against_support", "custom_default_is_billable"],
			as_dict=True,
		)
		if flags:
			row.custom_counts_against_support = flags.custom_counts_against_support
			row.is_billable = flags.custom_default_is_billable
