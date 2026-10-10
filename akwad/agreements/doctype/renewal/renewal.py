# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days

from akwad.service_utils import OPEN_RENEWAL_STATUSES, RENEWAL_LEAD_DAYS, RENEWAL_TERMINAL_STATUSES


class Renewal(Document):
	def validate(self):
		self.set_defaults_from_agreement()
		self.validate_new_agreement()
		self.validate_not_duplicate()

	def before_submit(self):
		if self.status not in RENEWAL_TERMINAL_STATUSES:
			frappe.throw(
				_("Only a Renewal with status {0} can be submitted.").format(" / ".join(RENEWAL_TERMINAL_STATUSES))
			)
		if self.status in ("Renewed", "Upgraded") and not self.new_agreement:
			frappe.throw(_("New Agreement is required to submit as {0}.").format(self.status))
		self.next_action_date = None

	def on_submit(self):
		if self.status in ("Renewed", "Upgraded") and self.new_agreement:
			frappe.db.set_value("Service Agreement", self.agreement, "status", "Renewed")

	def set_defaults_from_agreement(self):
		# Fallback defaults
		end_date, account_owner = frappe.db.get_value("Service Agreement", self.agreement, ["end_date", "account_owner"])
		if not self.due_date:
			self.due_date = add_days(end_date, -RENEWAL_LEAD_DAYS)
		if not self.follow_up_by:
			self.follow_up_by = account_owner

	def validate_not_duplicate(self):
		if not self.is_new():
			return
		existing = frappe.db.get_value(
			"Renewal", {"agreement": self.agreement, "docstatus": 0, "status": ("in", OPEN_RENEWAL_STATUSES)}, "name"
		)
		if existing:
			frappe.throw(_("{0} is already open for this agreement.").format(existing))

	def validate_new_agreement(self):
		if not self.new_agreement:
			return
		if self.new_agreement == self.agreement:
			frappe.throw(_("New Agreement must be different from the agreement being renewed."))
		customers = frappe.get_all(
			"Service Agreement", filters={"name": ("in", [self.agreement, self.new_agreement])}, pluck="customer"
		)
		if len(set(customers)) > 1:
			frappe.throw(_("New Agreement must be for the same customer."))
