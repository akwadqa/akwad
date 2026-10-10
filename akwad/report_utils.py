# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

#-------------- Column & Filter Helpers ----------------------------------------

import frappe

LIVE_STATUSES = ("Active", "Expiring Soon", "Expired")


def col(label, fieldname, fieldtype="Data", options=None, width=120):
	column = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, "width": width}
	if options:
		column["options"] = options
	return column


def pct(numerator, denominator):
	# Percentage rounded to one decimal point
	return round(numerator / denominator * 100, 1) if denominator else None


def agreement_filters(filters, **extra):
	# Agreement-level filters shared by reports: customer, agreement type, agreement."""
	out = dict(extra)
	for key in ("customer", "agreement_type"):
		if filters.get(key):
			out[key] = filters[key]
	if filters.get("agreement"):
		out["name"] = filters["agreement"]
	return out


def in_clause(names):
	# Safe Placeholder for an `in (...)` list
	return names or ["__none__"]


def site_names(sites):
	sites = [s for s in set(sites) if s]
	if not sites:
		return {}
	return dict(frappe.get_all("Site", filters={"name": ("in", sites)}, fields=["name", "site_name"], as_list=True))
