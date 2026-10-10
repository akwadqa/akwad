// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Support Consumption"] = {
	filters: [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -12)
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "agreement",
			"label": "Agreement",
			"fieldtype": "Link",
			"options": "Service Agreement"
		},
		{
			"fieldname": "over_allowance_only",
			"label": "Over Allowance Only",
			"fieldtype": "Check"
		}
	],
};
