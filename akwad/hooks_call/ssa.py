from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
from datetime import timedelta

@frappe.whitelist(allow_guest=True)
def calculate_gross_salary(self,method):
    self.ind_gross_salary=self.base+self.ind_allowance1+self.ind_allowance2+self.ind_allowance3+self.ind_allowance4+self.ind_allowance5+self.ind_allowance6+self.ind_allowance7