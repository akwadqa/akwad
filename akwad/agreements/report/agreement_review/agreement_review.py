# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from akwad.report_utils import col, pct
from akwad.service_utils import OVER_ALLOWANCE_MONTHS_THRESHOLD

# Figures come from Usage Summary (one per closed month), so the review reflects closed months only.
# Flags are for manual evaluation; nothing here blocks or enforces anything.
# No contract value is tracked yet, so this is a technical-cost/effort view, not a profitability one.


def execute(filters=None):
	filters = frappe._dict(filters or {})
	agreement = frappe.get_doc("Service Agreement", filters.agreement)
	agreement.check_permission("read")
	as_of = getdate(filters.get("as_of_date") or nowdate())

	summaries = frappe.get_all(
		"Usage Summary",
		filters={"agreement": agreement.name, "period_end": ("<=", as_of)},
		fields=["*"],
		order_by="period_start",
	)
	rows = [monthly_row(s) for s in summaries]
	total = total_row(rows, agreement, OVER_ALLOWANCE_MONTHS_THRESHOLD)
	data = rows + ([total] if rows else [])

	return get_columns(), data, None, None, get_summary(agreement, summaries, total, as_of)


def get_columns():
	money = lambda label, name: col(label, name, "Currency", width=110)  # noqa: E731
	return [
		col("Month", "month", width=80),
		col("Effort Hours", "effort_hours", "Float", width=100),
		money("Effort Cost", "effort_cost"),
		money("Hosting Cost", "hosting_cost"),
		col("Effort Margin (Hrs)", "margin", "Float", width=120),
		col("Support Used", "support_used", "Float", width=100),
		col("Support Allowed", "support_allowed", "Float", width=110),
		col("Visits Used", "visits_used", "Int", width=90),
		col("Visits Allowed", "visits_allowed", "Int", width=100),
		col("Out of Coverage Hrs", "out_of_coverage", "Float", width=130),
		col("Storage Peak (GB)", "storage_peak", "Float", width=120),
		col("Storage Allowed (GB)", "storage_allowed", "Float", width=130),
		col("Flags", "flags", width=340),
	]


def monthly_row(s):
	flags = []
	if flt(s.support_hours_excess) > 0:
		flags.append("Support over allowance")
	if flt(s.visits_excess) > 0:
		flags.append("Visits over allowance")
	if flt(s.storage_allowed_gb) and flt(s.storage_peak_gb) > flt(s.storage_allowed_gb):
		flags.append("Storage above allowance")
	if flt(s.margin) < 0:
		flags.append("Effort over support allowance")
	if flt(s.effort_hours_out_of_coverage) > 0:
		flags.append("Out-of-coverage hours")
	return {
		"month": s.period_month,
		"effort_hours": s.effort_hours_total,
		"effort_cost": s.effort_cost,
		"hosting_cost": s.hosting_cost,
		"margin": s.margin,
		"support_used": s.support_hours_used,
		"support_allowed": s.support_hours_allowed,
		"visits_used": s.visits_used,
		"visits_allowed": s.visits_allowed,
		"out_of_coverage": s.effort_hours_out_of_coverage,
		"storage_peak": s.storage_peak_gb,
		"storage_allowed": s.storage_allowed_gb,
		"flags": ", ".join(flags),
		"_over_allowance": bool(flt(s.support_hours_excess) > 0 or flt(s.visits_excess) > 0),
	}


def total_row(rows, agreement, months_threshold):
	def total(key):
		return sum(flt(r[key]) for r in rows)

	support_used, support_allowed = total("support_used"), total("support_allowed")
	margin = total("margin")
	months_over = sum(1 for r in rows if r["_over_allowance"])
	peak = max((flt(r["storage_peak"]) for r in rows), default=0)

	flags = []
	if support_allowed and support_used > support_allowed:
		flags.append("Support utilisation over 100%")
	if months_over >= months_threshold:
		flags.append(f"{months_over} months over allowance")
	if flt(agreement.storage_gb) and peak > flt(agreement.storage_gb):
		flags.append("Storage above allowance")
	if margin < 0:
		flags.append("Effort over support allowance")
	if total("out_of_coverage") > 0:
		flags.append("Out-of-coverage hours")

	return {
		"month": _("Total"),
		"effort_hours": total("effort_hours"),
		"effort_cost": total("effort_cost"),
		"hosting_cost": total("hosting_cost"),
		"margin": margin,
		"support_used": support_used,
		"support_allowed": support_allowed,
		"visits_used": sum(r["visits_used"] or 0 for r in rows),
		"visits_allowed": sum(r["visits_allowed"] or 0 for r in rows),
		"out_of_coverage": total("out_of_coverage"),
		"storage_peak": peak,
		"storage_allowed": agreement.storage_gb,
		"flags": ", ".join(flags),
		"bold": 1,
	}


def get_summary(agreement, summaries, total, as_of):
	if not summaries:
		return [{"value": 0, "label": _("No Usage Summaries up to {0}").format(as_of), "datatype": "Int"}]

	utilisation = pct(total["support_used"], total["support_allowed"])
	outstanding = frappe.db.count(
		"Ticket",
		{"agreement": agreement.name, "raised_on": ("<=", f"{as_of} 23:59:59"), "status": ("not in", ("Resolved", "Closed"))},
	)
	return [
		{"value": total["effort_cost"] + total["hosting_cost"], "label": _("Technical Cost to Date"), "datatype": "Currency"},
		{"value": total["margin"], "label": _("Effort Margin (Hrs)"), "datatype": "Float",
		 "indicator": "Red" if total["margin"] < 0 else "Green"},
		{"value": utilisation or 0,
		 "label": _("Support Utilisation ({0} of {1} h)").format(round(total["support_used"], 1), round(total["support_allowed"], 1)),
		 "datatype": "Percent", "indicator": "Red" if utilisation and utilisation > 100 else "Green"},
		{"value": total["visits_used"],
		 "label": _("Visits Used (of {0} allowed)").format(total["visits_allowed"]), "datatype": "Int",
		 "indicator": "Orange" if total["visits_used"] > total["visits_allowed"] else "Blue"},
		{"value": total["storage_peak"],
		 "label": _("Storage Peak GB (allowed {0})").format(flt(agreement.storage_gb) or _("n/a")), "datatype": "Float",
		 "indicator": "Red" if flt(agreement.storage_gb) and total["storage_peak"] > flt(agreement.storage_gb) else "Blue"},
		{"value": total["out_of_coverage"], "label": _("Out-of-Coverage Hours Absorbed"), "datatype": "Float",
		 "indicator": "Orange" if total["out_of_coverage"] else "Blue"},
		{"value": outstanding, "label": _("Tickets Outstanding"), "datatype": "Int",
		 "indicator": "Orange" if outstanding else "Blue"},
	]
