# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

"""
	Scheduled jobs
"""

import frappe
from frappe.utils import add_months, get_first_day, nowdate

from akwad.backup_operations.doctype.backup_job.backup_job import refresh_status
from akwad.agreements.doctype.usage_summary.usage_summary import generate


def daily():
	for job in (update_agreement_statuses, refresh_backup_job_status):
		try:
			job()
		except Exception:
			frappe.log_error(title=f"Akwad daily job failed: {job.__name__}")


def update_agreement_statuses():
	# Recompute Service Agreement status from today's date (Active / Expiring Soon / Expired)
	for name in frappe.get_all(
		"Service Agreement", filters={"status": ("in", ("Active", "Expiring Soon", "Expired"))}, pluck="name"
	):
		try:
			doc = frappe.get_doc("Service Agreement", name)
			before = doc.status
			doc.set_status()
			if doc.status != before:
				doc.save(ignore_permissions=True)
				frappe.db.commit()  # nosemgrep
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Could not refresh status of {name}")


def refresh_backup_job_status():
	for job in frappe.get_all("Backup Job", pluck="name"):
		refresh_status(job)


def notify_backups_due():
	"""
	09:00 daily: email a digest of Backup Jobs due today or overdue.

	A job is due unless a successful Backup Run log exists within its own window. 
	Checked directly against Backup Log, not the cached last_successful_backup rollup.

	Recipients are a placeholder currently until the notification design is finalized.
	"""
	from frappe.utils import add_days, add_months, getdate

	today = getdate(nowdate())
	due = []
	for job in frappe.get_all(
		"Backup Job",
		filters={"enabled": 1},
		fields=["name", "site", "server", "scope", "content", "frequency", "last_successful_backup", "creation"],
	):
		if not job.frequency:
			continue
		window_start = add_days(today, -1) if job.frequency == "Daily" else add_months(today, -1)
		if getdate(job.creation) > window_start:
			continue  # too new to expect a run yet
		if frappe.db.exists(
			"Backup Log",
			{
				"backup_job": job.name,
				"log_type": "Backup Run",
				"status": "Success",
				"log_datetime": (">=", window_start),
			},
		):
			continue
		due.append(job)

	if not due:
		return

	recipients = frappe.get_all(
		"Has Role", filters={"role": "Service Manager", "parenttype": "User"}, pluck="parent"
	)
	recipients = [r for r in recipients if r not in ("Administrator", "Guest") and frappe.db.get_value("User", r, "enabled")]
	if not recipients:
		return

	rows = "".join(
		f"<tr><td><a href='{frappe.utils.get_url()}/app/backup-job/{j.name}'>{j.name}</a></td>"
		f"<td>{j.site or j.server or ''}</td><td>{j.scope} / {j.content}</td><td>{j.frequency}</td>"
		f"<td>{j.last_successful_backup or 'Never'}</td></tr>"
		for j in due
	)
	message = (
		f"<p>{len(due)} backup job(s) are due today or overdue.</p>"
		"<table class='table table-bordered'><tr><th>Backup Job</th><th>Site / Server</th>"
		f"<th>Scope / Content</th><th>Frequency</th><th>Last Successful Backup</th></tr>{rows}</table>"
	)
	frappe.sendmail(recipients=recipients, subject=f"{len(due)} Backup Job(s) due", message=message)


def generate_monthly_usage_summaries():
	# 1st of the month
	period_start = get_first_day(add_months(nowdate(), -1))
	month = period_start.strftime("%Y-%m")

	for agreement in frappe.get_all(
		"Service Agreement",
		filters={
			"status": ("in", ("Active", "Expiring Soon", "Expired", "Renewed")),
			"start_date": ("<=", frappe.utils.get_last_day(period_start)),
			"end_date": (">=", period_start),
		},
		pluck="name",
	):
		if frappe.db.exists("Usage Summary", {"agreement": agreement, "period_month": month}):
			continue
		try:
			generate(agreement, month)
			frappe.db.commit()  # nosemgrep
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Usage Summary {month} failed for {agreement}")
