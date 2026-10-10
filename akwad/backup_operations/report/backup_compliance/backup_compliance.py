# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime, time_diff_in_hours

from akwad.report_utils import col

FREQUENCY_HOURS = {"Hourly": 1, "Every 6 Hours": 6, "Daily": 24, "Weekly": 168, "Monthly": 744}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		col("Customer", "customer", "Link", "Customer", 140),
		col("Site", "site", "Link", "Site", 100),
		col("Server", "server", "Link", "Server", 130),
		col("Backup Job", "job", "Link", "Backup Job", 100),
		col("Scope", "scope", width=90),
		col("Content", "content", width=80),
		col("Frequency", "frequency", width=110),
		col("Retention (Days)", "retention_days", "Int", width=120),
		col("Enabled", "enabled", "Check", width=70),
		col("Last Successful Backup", "last_successful_backup", "Datetime", width=160),
		col("Last Verified", "last_verified_on", "Date", width=95),
		col("Verification Result", "verification_result", width=120),
		col("Status", "status", width=110),
		col("Issues", "issues", width=280),
	]


def get_data(filters):
	site_customers = dict(frappe.get_all("Site", fields=["name", "customer"], as_list=True))
	server_customers = {}
	for row in frappe.get_all("Site", filters={"server": ("is", "set")}, fields=["server", "customer"]):
		server_customers.setdefault(row.server, set()).add(row.customer)

	job_filters = {}
	if filters.get("site"):
		job_filters["site"] = filters["site"]

	jobs = frappe.get_all(
		"Backup Job",
		filters=job_filters,
		fields=["name", "site", "server", "scope", "content", "frequency", "retention_days", "enabled",
		        "last_successful_backup", "last_verified_on", "last_verification_result"],
	)

	data = []
	for job in jobs:
		customer = site_customers.get(job.site)
		if not customer and job.server:
			customers = server_customers.get(job.server) or set()
			customer = ", ".join(sorted(customers)) or None
		if filters.get("customer") and filters["customer"] not in (customer or ""):
			continue

		issues = check(job)
		row = {
			"customer": customer,
			"site": job.site,
			"server": job.server,
			"job": job.name,
			"scope": job.scope,
			"content": job.content,
			"frequency": job.frequency,
			"retention_days": job.retention_days,
			"enabled": job.enabled,
			"last_successful_backup": job.last_successful_backup,
			"last_verified_on": job.last_verified_on,
			"verification_result": job.last_verification_result,
			"status": "Issues" if issues else "OK",
			"issues": "; ".join(issues),
		}
		if issues or not filters.get("issues_only"):
			data.append(row)
	return data


def check(job):
	issues = []
	if not job.enabled:
		issues.append("Job disabled")
	if not job.last_successful_backup:
		issues.append("No successful backup logged")
	else:
		job_hours = FREQUENCY_HOURS.get(job.frequency)
		if job_hours:
			age = time_diff_in_hours(now_datetime(), job.last_successful_backup)
			if age > 2 * job_hours:
				issues.append("Backup stale")
	if job.last_verification_result == "Fail":
		issues.append("Last verification failed")
	elif not job.last_verified_on:
		issues.append("Never verified")
	return issues
