// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Effort by Agreement and Activity Type"] = {
	filters: [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
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
			"fieldname": "activity_type",
			"label": "Activity Type",
			"fieldtype": "Link",
			"options": "Activity Type"
		},
		{
			"fieldname": "employee",
			"label": "Employee",
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "group_by_employee",
			"label": "Group by Employee",
			"fieldtype": "Check"
		}
	],
};
