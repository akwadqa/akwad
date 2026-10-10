// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Site and Server Register"] = {
	filters: [
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nActive\nSuspended\nDecommissioned"
		},
		{
			"fieldname": "application_platform",
			"label": "Application Platform",
			"fieldtype": "Select",
			"options": "\nFrappe\nERPNext"
		},
		{
			"fieldname": "environment",
			"label": "Environment",
			"fieldtype": "Select",
			"options": "\nProduction\nStaging\nDevelopment"
		},
		{
			"fieldname": "hosting_provider",
			"label": "Hosting Provider",
			"fieldtype": "Link",
			"options": "Hosting Provider"
		}
	],
};
