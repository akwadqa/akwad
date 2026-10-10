# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BackupJob(Document):
	def validate(self):
		if self.scope == "Application" and not self.site:
			frappe.throw(_("Site is required for an Application backup."))
		if self.scope == "Server" and not self.server:
			frappe.throw(_("Server is required for a Server backup."))

		# One job per (site, server, scope, content);
		duplicate = frappe.db.exists(
			"Backup Job",
			{
				"site": self.site or ("is", "not set"),
				"server": self.server or ("is", "not set"),
				"scope": self.scope,
				"content": self.content,
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			frappe.throw(_("{0} already covers this site, server, scope and content.").format(duplicate))


def refresh_status(job: str):
	# From last successful Backup Log
	last_run = frappe.db.get_value(
		"Backup Log",
		{"backup_job": job, "log_type": "Backup Run", "status": "Success"},
		"log_datetime",
		order_by="log_datetime desc",
	)
	verification = frappe.db.get_value(
		"Backup Log",
		{"backup_job": job, "log_type": "Verification"},
		["log_datetime", "checked_by", "result"],
		order_by="log_datetime desc",
		as_dict=True,
	)
	values = {
		"last_successful_backup": last_run,
		"last_verified_on": verification.log_datetime.date() if verification else None,
		"last_verified_by": verification.checked_by if verification else None,
		"last_verification_result": verification.result if verification else None,
	}
	frappe.db.set_value("Backup Job", job, values, update_modified=False)
