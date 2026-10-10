// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Coverage by Customer and Site"] = {
	filters: [
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "site",
			"label": "Site",
			"fieldtype": "Link",
			"options": "Site"
		},
		{
			"fieldname": "agreement_type",
			"label": "Agreement Type",
			"fieldtype": "Select",
			"options": "\nAMC\nWarranty"
		},
		{
			"fieldname": "as_of_date",
			"label": "As of Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "include_inactive",
			"label": "Include Draft, Cancelled and Renewed",
			"fieldtype": "Check"
		}
	],
};
