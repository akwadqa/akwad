# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from akwad.service_utils import validate_site_matches_agreement


class ServiceRecord(Document):
	def validate(self):
		validate_site_matches_agreement(self)
		for row in self.participants:
			if row.participant_type == "Employee" and row.employee and not row.person_name:
				row.person_name = frappe.db.get_value("Employee", row.employee, "employee_name")
