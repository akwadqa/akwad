# Copyright (c) 2013, Taazur and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Task ID") + ":Link/Task:150",
		_("Task Name") + ":Data:330",
#	_("Weight") + ":Float:80",
#	_("Progress%") + ":Float:100",
#	_("Overall%") + ":Float:100",
#	_("Start Date") + ":Date:100",
#	_("End Date") + ":Date:100",
		_("Status") + ":Data:100",
        _("Assigned To") + ":Data:140",
		_("Project") + ":Data:250",
        _("Expected Start Date") + ":Data:150",
		_("Description") + ":Data:1000"
	]

def get_data(filters):
	project=filters.get("project")
	return frappe.db.sql("""
	select
	A.name,
	A.subject,
#A.task_weight,
#A.progress,
#A.task_weight*A.progress/100,
#A.exp_start_date,
#A.exp_end_date,
	A.status,
    A.assigned_to,
	A.project,
    A.exp_start_date,
    A.description

	FROM
	`tabTask` as A
    WHERE
    A.project="%s"
    ORDER BY A.name DESC
	""" %(project), as_list=1)