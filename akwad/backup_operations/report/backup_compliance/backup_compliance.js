// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Backup Compliance"] = {
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
			"fieldname": "issues_only",
			"label": "Issues Only",
			"fieldtype": "Check"
		}
	],
};
