// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Expiring Agreements and Warranties"] = {
	filters: [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), 180)
		},
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "agreement_type",
			"label": "Agreement Type",
			"fieldtype": "Select",
			"options": "\nAMC\nWarranty"
		},
		{
			"fieldname": "account_owner",
			"label": "Account Owner",
			"fieldtype": "Link",
			"options": "User"
		}
	],
};
