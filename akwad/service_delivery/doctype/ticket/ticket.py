# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from akwad.service_utils import validate_site_matches_agreement


class Ticket(Document):
	def validate(self):
		validate_site_matches_agreement(self)
