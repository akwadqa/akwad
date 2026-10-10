# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from akwad.backup_operations.doctype.backup_job.backup_job import refresh_status

RESULT_TO_STATUS = {"Pass": "Success", "Fail": "Failed", "Partial": "Partial"}


class BackupLog(Document):
	def validate(self):
		if self.log_type == "Verification":
			if not self.result:
				frappe.throw(_("Result is required for a Verification log."))
			self.checked_by = self.checked_by or frappe.session.user
			self.status = self.status or RESULT_TO_STATUS[self.result]

	def on_update(self):
		refresh_status(self.backup_job)

	def after_delete(self):
		refresh_status(self.backup_job)
