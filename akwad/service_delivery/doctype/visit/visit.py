# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours

from akwad.service_utils import month_of, validate_site_matches_agreement


class Visit(Document):
	def validate(self):
		validate_site_matches_agreement(self)
		self.allowance_month = month_of(self.visit_date)
		if self.start_time and self.end_time:
			if str(self.end_time) <= str(self.start_time):
				frappe.throw(_("End Time must be after Start Time."))
			if not self.duration_hrs:
				self.duration_hrs = round(time_diff_in_hours(self.end_time, self.start_time), 2)
		# Visit Employee.hours is an attendance roster only; allowances read Timesheet.

	def on_submit(self):
		self.db_set("status", "Completed")

	def on_cancel(self):
		self.db_set("status", "Cancelled")
