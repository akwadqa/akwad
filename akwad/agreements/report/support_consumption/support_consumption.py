# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe

from akwad.report_utils import agreement_filters, col, pct


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		col("Agreement", "agreement", "Link", "Service Agreement", 150),
		col("Customer", "customer", "Link", "Customer", 150),
		col("Month", "period_month", width=80),
		col("Allowed (Month)", "support_hours_allowed", "Float", width=110),
		col("Used (Month)", "support_hours_used", "Float", width=100),
		col("Remaining (Month)", "support_hours_remaining", "Float", width=120),
		col("Excess", "support_hours_excess", "Float", width=80),
		col("Allowed (Term)", "support_hours_allowed_term", "Float", width=110),
		col("Used (Term)", "support_hours_used_term", "Float", width=100),
		col("Remaining (Term)", "support_hours_remaining_term", "Float", width=120),
		col("Term Utilisation %", "term_utilisation", "Percent", width=120),
	]


def get_data(filters):
	conditions = agreement_filters(filters)
	conditions.pop("agreement_type", None)
	if conditions.get("name"):
		conditions["agreement"] = conditions.pop("name")
	if filters.get("from_date"):
		conditions["period_start"] = (">=", filters.from_date)
	if filters.get("to_date"):
		conditions["period_end"] = ("<=", filters.to_date)
	if filters.get("over_allowance_only"):
		conditions["support_hours_excess"] = (">", 0)

	rows = frappe.get_list(
		"Usage Summary",
		filters=conditions,
		fields=[c["fieldname"] for c in get_columns() if c["fieldname"] != "term_utilisation"],
		order_by="period_start desc, agreement",
	)
	for row in rows:
		row.term_utilisation = pct(row.support_hours_used_term, row.support_hours_allowed_term)
	return rows
