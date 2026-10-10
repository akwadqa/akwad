# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff, nowdate

from akwad.report_utils import col
from akwad.service_utils import OPEN_RENEWAL_STATUSES


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		col("Agreement", "agreement", "Link", "Service Agreement", 150),
		col("Customer", "customer", "Link", "Customer", 150),
		col("Type", "agreement_type", width=100),
		col("Start", "start_date", "Date", width=95),
		col("Expires", "end_date", "Date", width=95),
		col("Days Left", "days_left", "Int", width=80),
		col("Account Owner", "account_owner", "Link", "User", 150),
		col("Renewal", "renewal", "Link", "Renewal", 130),
		col("Renewal Status", "renewal_status", width=110),
	]


def get_data(filters):
	conditions, values = [], {"from_date": filters.get("from_date") or nowdate(), "to_date": filters.get("to_date")}
	for key, column in (
		("customer", "customer"),
		("agreement_type", "agreement_type"),
		("account_owner", "account_owner"),
	):
		if filters.get(key):
			conditions.append(f"and {column} = %({key})s")
			values[key] = filters[key]
	if values["to_date"]:
		conditions.append("and end_date <= %(to_date)s")

	rows = frappe.db.sql(
		f"""
		select name as agreement, customer, agreement_type, account_owner, start_date, end_date
		from `tabService Agreement`
		where status in ('Active', 'Expiring Soon', 'Expired') and end_date >= %(from_date)s {" ".join(conditions)}
		order by end_date, name
		""",
		values,
		as_dict=True,
	)

	renewals = {}
	for r in frappe.get_all(
		"Renewal",
		filters={"agreement": ("in", [row.agreement for row in rows] or ["__none__"]), "docstatus": 0},
		fields=["name", "agreement", "status"],
		order_by="creation",
	):
		if r.status in OPEN_RENEWAL_STATUSES:
			renewals[r.agreement] = r

	today = nowdate()
	for row in rows:
		row.days_left = date_diff(row.end_date, today)
		renewal = renewals.get(row.agreement)
		row.renewal = renewal.name if renewal else None
		row.renewal_status = renewal.status if renewal else None
	return rows
