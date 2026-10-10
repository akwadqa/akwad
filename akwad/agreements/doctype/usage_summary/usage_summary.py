# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_months,
	flt,
	get_first_day,
	get_last_day,
	getdate,
	nowdate,
)

from akwad.service_utils import agreement_year_start, term_months


class UsageSummary(Document):
	def validate(self):
		if not self.flags.from_generate and self.is_new():
			frappe.throw(_("Usage Summaries are generated from the Service Agreement, not entered by hand."))
		if self.is_new() and frappe.db.exists(
			"Usage Summary", {"agreement": self.agreement, "period_month": self.period_month}
		):
			frappe.throw(_("A Usage Summary for {0} / {1} already exists.").format(self.agreement, self.period_month))


def _timesheet_rows(agreement, start, end, extra=""):
	return frappe.db.sql(
		f"""
		select td.activity_type, sum(td.hours) as hours, sum(td.costing_amount) as cost,
			max(td.custom_counts_against_support) as counts_against_support
		from `tabTimesheet Detail` td
		join `tabTimesheet` ts on ts.name = td.parent
		where ts.docstatus = 1 and td.custom_agreement = %(agreement)s
			and date(td.from_time) between %(start)s and %(end)s {extra}
		group by td.activity_type
		""",
		{"agreement": agreement, "start": start, "end": end},
		as_dict=True,
	)


def generate(agreement_name: str, month: str | None = None) -> str:
	#Usage summary per Agreement-Closed Month

	agreement = frappe.get_doc("Service Agreement", agreement_name)
	agreement.check_permission("write")

	if month:
		period_start = get_first_day(getdate(month + "-01"))
	else:
		period_start = get_first_day(add_months(nowdate(), -1))
	period_end = get_last_day(period_start)
	month = period_start.strftime("%Y-%m")

	if period_end >= getdate(nowdate()):
		frappe.throw(_("{0} is not a closed month yet.").format(month))
	if getdate(agreement.start_date) > period_end or getdate(agreement.end_date) < period_start:
		frappe.throw(_("{0} falls outside the agreement term.").format(month))
	if frappe.db.exists("Usage Summary", {"agreement": agreement, "period_month": month}):
		frappe.throw(_("A Usage Summary for {0} already exists and is never regenerated.").format(month))

	months_in_term = term_months(agreement.start_date, agreement.end_date)
	# Service Agreement is customer-level only; hosting figures are read from all of the customer's sites.
	sites = frappe.get_all("Site", filters={"customer": agreement.customer}, pluck="name")
	doc = frappe.new_doc("Usage Summary")
	doc.flags.from_generate = True
	doc.update(
		{
			"agreement": agreement.name,
			"customer": agreement.customer,
			"period_month": month,
			"period_start": period_start,
			"period_end": period_end,
			"generated_on": frappe.utils.now_datetime(),
		}
	)

	# Support: Timesheet Detail hours flagged custom_counts_against_support, for submitted timesheets only.
	# support_hours is a monthly allowance.
	counted = " and td.custom_counts_against_support = 1"
	used_month = sum(flt(r.hours) for r in _timesheet_rows(agreement.name, period_start, period_end, counted))
	used_term = sum(flt(r.hours) for r in _timesheet_rows(agreement.name, agreement.start_date, period_end, counted))
	allowed_month = flt(agreement.support_hours)
	allowed_term = allowed_month * months_in_term
	doc.update(
		{
			"support_hours_allowed": allowed_month,
			"support_hours_used": used_month,
			"support_hours_remaining": max(0, allowed_month - used_month),
			"support_hours_excess": max(0, used_month - allowed_month),
			"support_hours_allowed_term": allowed_term,
			"support_hours_used_term": used_term,
			"support_hours_remaining_term": max(0, allowed_term - used_term),
		}
	)

	# Visits: submitted, completed visits that count against the allowance. Not added to support hours.
	def visit_stats(start, end):
		visits = frappe.get_all(
			"Visit",
			filters={
				"agreement": agreement.name,
				"docstatus": 1,
				"status": "Completed",
				"counts_against_allowance": 1,
				"visit_date": ("between", (start, end)),
			},
			fields=["duration_hrs"],
		)
		return len(visits), sum(flt(v.duration_hrs) for v in visits)

	visits_used, visit_hours = visit_stats(period_start, period_end)
	_count, year_hours = visit_stats(agreement_year_start(agreement.start_date, period_end), period_end)
	doc.update(
		{
			"visits_allowed": agreement.visits_per_month or 0,
			"visits_used": visits_used,
			"visits_excess": max(0, visits_used - (agreement.visits_per_month or 0)),
			"visit_hours": visit_hours,
			"visit_hours_term_to_date": year_hours,
		}
	)

	# Tickets
	doc.update(
		{
			"tickets_opened": frappe.db.count(
				"Ticket", {"agreement": agreement.name, "raised_on": ("between", (period_start, str(period_end) + " 23:59:59"))}
			),
			# Ticket current status
			"tickets_resolved": frappe.db.count(
				"Ticket",
				{
					"agreement": agreement.name,
					"status": ("in", ("Resolved", "Closed")),
					"raised_on": ("between", (period_start, str(period_end) + " 23:59:59")),
				},
			),
			"tickets_outstanding": frappe.db.count(
				"Ticket",
				{
					"agreement": agreement.name,
					"status": ("not in", ("Resolved", "Closed")),
					"raised_on": ("<=", str(period_end) + " 23:59:59"),
				},
			),
		}
	)

	# Effort: all employee time on the agreement, covered or not.
	out_of_coverage = set(frappe.get_all("Activity Type", filters={"custom_is_out_of_coverage": 1}, pluck="name"))
	total = ooc = cost = 0.0
	for row in _timesheet_rows(agreement, period_start, period_end):
		doc.append(
			"effort_lines",
			{
				"activity_type": row.activity_type,
				"hours": row.hours,
				"counts_against_support": row.counts_against_support,
				"cost": row.cost,  # snapshotted costing_amount, never recomputed
			},
		)
		total += flt(row.hours)
		cost += flt(row.cost)
		if row.activity_type in out_of_coverage:
			ooc += flt(row.hours)
	doc.update({"effort_hours_total": total, "effort_hours_out_of_coverage": ooc, "effort_cost": cost})

	# Hosting: read from Hosting Usage Log across all of the customer sites.
	storage_used = storage_peak = bandwidth = hosting_cost = 0.0
	if sites:
		logs = frappe.get_all(
			"Hosting Usage Log",
			filters={"site": ("in", sites), "log_date": ("between", (period_start, period_end))},
			fields=["log_date", "files_size_gb", "db_size_gb", "bandwidth_gb", "actual_cost"],
			order_by="log_date",
		)
		by_day = {}
		for log in logs:
			by_day[log.log_date] = by_day.get(log.log_date, 0) + flt(log.files_size_gb) + flt(log.db_size_gb)
			bandwidth += flt(log.bandwidth_gb)
			hosting_cost += flt(log.actual_cost)
		if by_day:
			storage_used = by_day[max(by_day)]
			storage_peak = max(by_day.values())
	doc.update(
		{
			"storage_allowed_gb": agreement.storage_gb,
			"storage_used_gb": storage_used,
			"storage_peak_gb": storage_peak,
			"bandwidth_allowed_gb": agreement.bandwidth_gb,
			"bandwidth_used_gb": bandwidth,
			"hosting_cost": hosting_cost,
		}
	)

	# Effort margin: support hours allowed vs. all effort spent (covered and out-of-coverage). 
	# Effort_cost/hosting_cost stay as plain technical costs.
	doc.update({"margin": allowed_month - total})

	doc.insert(ignore_permissions=True)
	return doc.name
