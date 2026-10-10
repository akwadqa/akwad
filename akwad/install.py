# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

"""
	Roles, ERPNext custom fields and seed data (activity_type)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ROLES = ("Service Manager", "Service Delivery")

CUSTOM_FIELDS = {
	"Timesheet Detail": [
		dict(fieldname="custom_agreement", label="Agreement", fieldtype="Link", options="Service Agreement",
		     insert_after="activity_type", in_list_view=1),
		dict(fieldname="custom_customer", label="Customer", fieldtype="Link", options="Customer",
		     fetch_from="custom_agreement.customer", read_only=1, insert_after="custom_agreement"),
		dict(fieldname="custom_site", label="Site", fieldtype="Link", options="Site", insert_after="custom_customer"),
		dict(fieldname="custom_ticket", label="Ticket", fieldtype="Link", options="Ticket", insert_after="custom_site"),
		dict(fieldname="custom_visit", label="Visit", fieldtype="Link", options="Visit", insert_after="custom_ticket"),
		dict(fieldname="custom_counts_against_support", label="Counts Against Support", fieldtype="Check",
		     insert_after="custom_visit", description="Defaults from Activity Type"),
		dict(fieldname="custom_allowance_month", label="Allowance Month", fieldtype="Data", read_only=1,
		     insert_after="custom_counts_against_support", description="YYYY-MM"),
	],
	"Activity Type": [
		dict(fieldname="custom_counts_against_support", label="Counts Against Support", fieldtype="Check",
		     insert_after="billing_rate"),
		dict(fieldname="custom_is_visit", label="Is Visit", fieldtype="Check", insert_after="custom_counts_against_support"),
		dict(fieldname="custom_is_out_of_coverage", label="Is Out of Coverage", fieldtype="Check",
		     insert_after="custom_is_visit"),
		dict(fieldname="custom_default_is_billable", label="Default Is Billable", fieldtype="Check",
		     insert_after="custom_is_out_of_coverage"),
	],
}

# name: (counts_against_support, is_visit, is_out_of_coverage, default_is_billable, billing_rate)
ACTIVITY_TYPES = {
	"Coding": (1, 0, 0, 0, 0),
	"Assistance": (1, 0, 0, 0, 0),
	"Training": (1, 0, 0, 0, 0),
	"Maintenance": (1, 0, 0, 0, 0),
	"Warranty": (0, 0, 0, 0, 0),
	"Visit": (0, 1, 0, 0, 0),  # visit hours never reduce the support allowance
	"Out of Coverage": (0, 0, 1, 1, 150),
	"Internal": (0, 0, 0, 0, 0),
}


def before_migrate():
	# Roles must exist before DocType permissions referencing them are synced
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def after_migrate():
	create_custom_fields(CUSTOM_FIELDS)
	seed_activity_types()


def seed_activity_types():
	# Create missing Activity Types only; existing ones are left as configured
	for name, (counts, is_visit, out_of_coverage, billable, billing_rate) in ACTIVITY_TYPES.items():
		if frappe.db.exists("Activity Type", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Activity Type",
				"activity_type": name,
				"costing_rate": 60,
				"billing_rate": billing_rate,
				"custom_counts_against_support": counts,
				"custom_is_visit": is_visit,
				"custom_is_out_of_coverage": out_of_coverage,
				"custom_default_is_billable": billable,
			}
		).insert(ignore_permissions=True)
