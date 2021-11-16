// Copyright (c) 2016, Akwad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Task List"] = {
	"filters": [
	{
		"fieldname":"status",
		"Label":__("Status"),
		"fieldtype": "Select",
		"options": ["","Open","Working","Pending Review","Overview","Completed","Cancelled"],
		"default":""
	},
	
	{
		"fieldname":"project",
		"label": __("Project"),
		"fieldtype": "Link",
		"options":"Project",
		"default":"Open"
	},
	
	{
		"fieldname":"not_cancelled",
		"label": __("Not Cancelled"),
		"fieldtype": "Select",
		"options": ["Cancelled","Not Cancelled"],
		"default": "Not Cancelled"
	}


]
};