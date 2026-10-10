# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate

from akwad.report_utils import LIVE_STATUSES, agreement_filters, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		col("Customer", "customer", "Link", "Customer", 150),
		col("Site", "site", "Link", "Site", 110),
		col("Site Name", "site_name", width=150),
		col("Agreement", "agreement", "Link", "Service Agreement", 150),
		col("Type", "agreement_type", width=90),
		col("Agreement Status", "agreement_status", width=120),
		col("Start", "start_date", "Date", width=95),
		col("End", "end_date", "Date", width=95),
		col("Coverage", "coverage", width=100),
	]


def get_data(filters):
	as_of = getdate(filters.get("as_of_date") or nowdate())

	site_conditions = {}
	if filters.get("customer"):
		site_conditions["customer"] = filters["customer"]
	if filters.get("site"):
		site_conditions["name"] = filters["site"]
	sites = frappe.get_list(
		"Site", filters=site_conditions, fields=["name", "site_name", "customer"], order_by="customer, name"
	)
	if not sites:
		return []

	extra = {} if filters.get("include_inactive") else {"status": ("in", LIVE_STATUSES)}
	agreements = frappe.get_list(
		"Service Agreement",
		filters=agreement_filters(filters, **extra),
		fields=["name", "customer", "agreement_type", "status", "start_date", "end_date"],
		order_by="customer, name",
	)
	by_customer = {}
	for a in agreements:
		by_customer.setdefault(a.customer, []).append(a)

	data = []
	for site in sites:
		for a in by_customer.get(site.customer, []):
			if getdate(a.start_date) > as_of:
				coverage = "Not Yet"
			elif getdate(a.end_date) < as_of:
				coverage = "Expired"
			else:
				coverage = "Covered"
			data.append(
				{
					"customer": site.customer,
					"site": site.name,
					"site_name": site.site_name,
					"agreement": a.name,
					"agreement_type": a.agreement_type,
					"agreement_status": a.status,
					"start_date": a.start_date,
					"end_date": a.end_date,
					"coverage": coverage,
				}
			)
	return data
