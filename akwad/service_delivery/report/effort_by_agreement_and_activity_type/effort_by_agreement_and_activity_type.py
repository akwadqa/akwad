# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, nowdate

from akwad.report_utils import col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(filters), get_data(filters)


def get_columns(filters):
	columns = [
		col("Customer", "customer", "Link", "Customer", 150),
		col("Agreement", "agreement", "Link", "Service Agreement", 150),
		col("Activity Type", "activity_type", "Link", "Activity Type", 140),
	]
	if filters.get("group_by_employee"):
		columns.append(col("Employee", "employee", "Link", "Employee", 130))
	return columns + [
		col("Hours", "hours", "Float", width=80),
		col("Counted Against Support", "support_hours", "Float", width=150),
		col("Billable Hours", "billable_hours", "Float", width=110),
		col("Out of Coverage", "out_of_coverage", "Check", width=110),
		col("Cost", "cost", "Currency", width=100),
		col("Billing Amount", "billing_amount", "Currency", width=110),
	]


def get_data(filters):
	values = {
		"from_date": filters.get("from_date") or add_months(nowdate(), -1),
		"to_date": filters.get("to_date") or nowdate(),
	}
	conditions = []
	for key, column in (
		("customer", "td.custom_customer"),
		("agreement", "td.custom_agreement"),
		("activity_type", "td.activity_type"),
		("employee", "ts.employee"),
	):
		if filters.get(key):
			conditions.append(f"and {column} = %({key})s")
			values[key] = filters[key]

	by_employee = bool(filters.get("group_by_employee"))
	# All submitted employee time, covered or not. Cost is the snapshotted row value, never recomputed here.
	return frappe.db.sql(
		f"""
		select max(td.custom_customer) as customer, td.custom_agreement as agreement, td.activity_type,
			{"ts.employee as employee," if by_employee else ""}
			sum(td.hours) as hours,
			sum(case when td.custom_counts_against_support = 1 then td.hours else 0 end) as support_hours,
			sum(case when td.is_billable = 1 then td.hours else 0 end) as billable_hours,
			max(act.custom_is_out_of_coverage) as out_of_coverage,
			sum(td.costing_amount) as cost,
			sum(td.billing_amount) as billing_amount
		from `tabTimesheet Detail` td
		join `tabTimesheet` ts on ts.name = td.parent
		left join `tabActivity Type` act on act.name = td.activity_type
		where ts.docstatus = 1 and date(td.from_time) between %(from_date)s and %(to_date)s
			{" ".join(conditions)}
		group by td.custom_agreement, td.activity_type {", ts.employee" if by_employee else ""}
		order by td.custom_agreement, td.activity_type
		""",
		values,
		as_dict=True,
	)
