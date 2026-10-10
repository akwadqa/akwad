# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, nowdate

from akwad.service_utils import OPEN_RENEWAL_STATUSES, RENEWAL_LEAD_DAYS


class ServiceAgreement(Document):
	def validate(self):
		self.set_title()
		self.validate_dates()
		self.set_warranty_end_date()
		self.set_status()

	def on_update(self):
		self.refresh_open_renewals()

	
	

	def set_title(self):
		self.title = f"{self.customer} - {self.agreement_type}" if self.customer else self.agreement_type

	def validate_dates(self):
		if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))

	def set_warranty_end_date(self):
		# Warranty end_date = start_date + warranty_months - 1 day. Warranty starts at the agreement start date.
		if self.agreement_type == "Warranty" and self.start_date and self.warranty_months:
			self.end_date = add_days(add_months(self.start_date, self.warranty_months), -1)

	def set_status(self):
		# Draft, Cancelled and Renewed are set explicitly; the rest follows the dates.
		if self.is_new() or self.status in ("Draft", "Cancelled", "Renewed") or not self.status:
			self.status = self.status or "Draft"
			return
		today = getdate(nowdate())
		if getdate(self.end_date) < today:
			self.status = "Expired"
		elif (getdate(self.end_date) - today).days <= RENEWAL_LEAD_DAYS:
			self.status = "Expiring Soon"
		else:
			self.status = "Active"

	def refresh_open_renewals(self):
		# Recompute the due date of open Renewals when the end date moves.
		before = self.get_doc_before_save()
		if before and before.end_date == self.end_date:
			return
		for name in frappe.get_all(
			"Renewal",
			filters={"agreement": self.name, "docstatus": 0, "status": ("in", OPEN_RENEWAL_STATUSES)},
			pluck="name",
		):
			frappe.db.set_value("Renewal", name, "due_date", add_days(self.end_date, -RENEWAL_LEAD_DAYS))

	# ---- Action Helpers --------------------------------------

	@frappe.whitelist()
	def activate(self):
		if self.status != "Draft":
			frappe.throw(_("Only a Draft agreement can be activated."))
		self.status = "Active"
		# validate() resets status if needed
		self.save()
		return self.status

	@frappe.whitelist()
	def cancel_agreement(self, reason: str | None = None):
		if self.status in ("Draft", "Cancelled", "Renewed"):
			frappe.throw(_("Agreement is {0}.").format(self.status))
		self.status = "Cancelled"
		self.save()
		if reason:
			self.add_comment("Comment", _("Cancelled: {0}").format(reason))

	@frappe.whitelist()
	def generate_usage_summary(self, month: str | None = None) -> str:
		from akwad.agreements.doctype.usage_summary.usage_summary import generate

		return generate(self.name, month)
