# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

"""Demo data that walks the whole workflow.

    bench --site <site> execute akwad.demo.make_demo_data

Safe to re-run: it stops if the demo customer already exists.
"""

import frappe
from frappe.utils import add_days, add_months, get_first_day, nowdate

from akwad.service_utils import RENEWAL_LEAD_DAYS

CUSTOMER = "Demo Customer (Akwad)"


def make_demo_data():
	if frappe.db.exists("Customer", CUSTOMER):
		print("Demo data already exists.")
		return

	last_month = get_first_day(add_months(nowdate(), -1))
	day = lambda n: add_days(last_month, n)  # noqa: E731

	def insert(doctype, **values):
		return frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)

	# Masters
	for doctype, key, name, extra in (
		("Hosting Provider", "provider_name", "AWS", {"website": "https://aws.amazon.com"}),
		("Domain Registrar", "registrar_name", "Demo Registrar", {}),
		("Backup Storage Location", "location_name", "S3 Backups (Frankfurt)", {"provider": "AWS", "region": "eu-central-1"}),
	):
		if not frappe.db.exists(doctype, name):
			insert(doctype, **{key: name}, **extra)

	# Hosting Plan and Support Plan templates
	hosting_plan = insert(
		"Hosting Plan",
		plan_name="Standard Hosting",
		description="Standard managed hosting allowance.",
		storage_gb=50,
		bandwidth_gb=200,
		backup_storage_gb=20,
	)
	support_plan = insert(
		"Support Plan",
		plan_name="Standard Support",
		description="Standard application support bundle.",
		support_hours=10,
		support_hours_window="9am-6pm Sun-Thu",
		visits_per_month=1,
		sla_resolution=[
			{"priority": "Normal", "response_time": 8, "resolution_time": 48},
			{"priority": "High", "response_time": 4, "resolution_time": 24},
			{"priority": "Urgent", "response_time": 1, "resolution_time": 8},
		],
	)

	# ERPNext side
	insert(
		"Customer",
		customer_name=CUSTOMER,
		customer_type="Company",
		customer_group=frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
		territory=frappe.db.get_value("Territory", {"is_group": 0}, "name"),
	)
	employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
	if not employee:
		employee = insert(
			"Employee",
			first_name="Demo Technician",
			gender=frappe.db.get_value("Gender", {}, "name"),
			date_of_birth="1990-01-01",
			date_of_joining="2024-01-01",
			company=frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name"),
		).name

	# Infrastructure: Site now models one environment directly (no child table).
	server = insert("Server", instance_name="demo-app-01", hosting_provider="AWS", region="eu-central-1",
	                instance_type="t3.large", server_ip="10.0.0.10", vcpu=2, ram_gb=8, disk_gb=100)
	site = insert(
		"Site",
		customer=CUSTOMER,
		site_name="Demo ERP",
		application_platform="ERPNext",
		domain="erp.demo.example",
		domain_registrar="Demo Registrar",
		environment="Production",
		url="https://erp.demo.example",
		server=server.name,
		available=1,
	)

	# Agreement: AMC, filled from the two plan templates (mirrors what the form's JS does on pick).
	agreement = insert(
		"Service Agreement",
		customer=CUSTOMER,
		agreement_type="AMC",
		account_owner="Administrator",
		start_date=add_months(last_month, -2),
		end_date=add_days(add_months(last_month, 10), -1),
		hosting_plan=hosting_plan.name,
		storage_gb=hosting_plan.storage_gb,
		bandwidth_gb=hosting_plan.bandwidth_gb,
		backup_storage_gb=hosting_plan.backup_storage_gb,
		support_plan=support_plan.name,
		support_hours=support_plan.support_hours,
		support_hours_window=support_plan.support_hours_window,
		visits_per_month=support_plan.visits_per_month,
		sla_resolution=[
			{"priority": r.priority, "response_time": r.response_time, "resolution_time": r.resolution_time}
			for r in support_plan.sla_resolution
		],
		services=[
			{"category": "Included Service", "service": "Application Support", "description": "Break-fix and how-to support during business hours."},
			{"category": "Included Module", "service": "Accounting"},
			{"category": "Included Module", "service": "HR & Payroll"},
			{"category": "Excluded Service", "service": "Custom Development", "description": "Billed separately on request."},
			{"category": "Backup Policy", "service": "Daily backup, 30-day retention", "value": "S3 Backups (Frankfurt)"},
		],
	)
	agreement.activate()

	# Warranty agreement: starts at the agreement's own start date, no separate correction flow.
	warranty = insert(
		"Service Agreement",
		customer=CUSTOMER,
		agreement_type="Warranty",
		account_owner="Administrator",
		start_date=last_month,
		warranty_months=12,
	)
	warranty.activate()

	# Backup assurance
	jobs = {
		content: insert("Backup Job", site=site.name, server=server.name, scope="Application", content=content,
		                frequency="Daily", retention_days=30, storage_location="S3 Backups (Frankfurt)")
		for content in ("Database", "Files")
	}
	for content, job in jobs.items():
		insert("Backup Log", backup_job=job.name, log_type="Backup Run", log_datetime=f"{day(10)} 02:00:00", status="Success",
		       db_size_gb=1.2 if content == "Database" else 0, files_size_gb=3.5 if content == "Files" else 0)
	insert("Backup Log", backup_job=jobs["Database"].name, log_type="Verification", log_datetime=f"{day(12)} 10:00:00",
	       result="Pass", verification_method="Restore to staging")

	# Hosting usage
	for n, files, db in ((5, 11.0, 3.0), (20, 12.0, 3.4)):
		insert("Hosting Usage Log", server=server.name, site=site.name, log_date=day(n), files_size_gb=files,
		       db_size_gb=db, bandwidth_gb=40, actual_cost=380, source="Manual")

	# Service delivery: a visit, a ticket, a service record
	visit = insert(
		"Visit", agreement=agreement.name, site=site.name, visit_date=day(8), start_time="09:00:00", end_time="12:00:00",
		purpose="Training", counts_against_allowance=1, work_completed="On-site training for the accounts team.",
		customer_signatory="Demo Signatory",
		employees=[{"employee": employee, "role_on_visit": "Lead", "hours": 3}],
	)
	visit.submit()
	insert("Ticket", subject="Invoice print format shows wrong VAT", agreement=agreement.name, site=site.name,
	       raised_on=f"{day(14)} 09:00:00", priority="High", category="Bug",
	       status="Resolved", assigned_to="Administrator")
	insert("Service Record", record_type="Training", title="Accounts team training", agreement=agreement.name,
	       site=site.name, record_date=day(8), duration_hrs=3, reference_type="Visit", reference_name=visit.name,
	       participants=[{"participant_type": "Employee", "employee": employee},
	                     {"participant_type": "Customer", "person_name": "Demo Signatory"}])

	# Time logging: support (counts), a visit (does not count), out-of-coverage work
	def log(activity, hours, start_day, hour):
		return {
			"activity_type": activity,
			"from_time": f"{day(start_day)} {hour:02d}:00:00",
			"to_time": f"{day(start_day)} {hour + hours:02d}:00:00",
			"hours": hours,
			"custom_agreement": agreement.name,
			"custom_site": site.name,
			"custom_visit": visit.name if activity == "Visit" else None,
		}

	timesheet = insert("Timesheet", employee=employee, time_logs=[
		log("Assistance", 3, 3, 9), log("Maintenance", 4, 6, 9), log("Visit", 3, 8, 9), log("Out of Coverage", 2, 15, 9),
	])
	timesheet.submit()

	# Usage summary for the closed month, then a renewal (pre-filled the way the form's link would)
	summary = agreement.generate_usage_summary(last_month.strftime("%Y-%m"))
	renewal = insert(
		"Renewal",
		agreement=agreement.name,
		due_date=add_days(agreement.end_date, -RENEWAL_LEAD_DAYS),
		follow_up_by=agreement.account_owner,
	)
	frappe.db.commit()
	print(f"Created agreement {agreement.name}, warranty {warranty.name}, {summary}, {renewal.name}")
