# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

"""
Ingestion endpoints for machine-generated logs.


    POST /api/method/akwad.api.log_hosting_usage   {"entries": [{...}, ...]}
    POST /api/method/akwad.api.log_backup          {"entries": [{...}, ...]}

Authenticate with an API key and secret of a Service Manager or Service Delivery User.
Each entry is saved on its own: one bad entry is reported back and does not stop the rest.

"""

import frappe
from frappe import _

MAX_ENTRIES = 500

HOSTING_FIELDS = (
	"server", "site", "log_date", "disk_used_gb", "files_size_gb", "db_size_gb",
	"avg_cpu", "avg_ram", "bandwidth_gb", "actual_cost",
)
BACKUP_FIELDS = (
	"backup_job", "log_type", "log_datetime", "status", "files_size_gb", "db_size_gb", "storage_location",
	"region", "retention_expiry", "external_ref", "checked_by", "verification_method", "result", "notes",
)


@frappe.whitelist(methods=["POST"])
def log_hosting_usage(entries):
	return ingest("Hosting Usage Log", entries, HOSTING_FIELDS, lambda e: {"source": "API"})


@frappe.whitelist(methods=["POST"])
def log_backup(entries):
	# Entry names its job directly (`backup_job`) or by `site` + `scope` + `content`
	return ingest("Backup Log", entries, BACKUP_FIELDS, resolve_backup_job)


def resolve_backup_job(entry):
	if entry.get("backup_job"):
		return {}
	job = frappe.db.get_value(
		"Backup Job",
		{"site": entry.get("site"), "scope": entry.get("scope"), "content": entry.get("content"), "enabled": 1},
		"name",
	)
	if not job:
		frappe.throw(_("No enabled Backup Job for site {0}, {1}, {2}.").format(entry.get("site"), entry.get("scope"), entry.get("content")))
	return {"backup_job": job}


def ingest(doctype, entries, allowed_fields, extras):
	entries = frappe.parse_json(entries)
	if isinstance(entries, dict):
		entries = [entries]
	if not isinstance(entries, list) or not entries:
		frappe.throw(_("Send a non-empty list of entries."))
	if len(entries) > MAX_ENTRIES:
		frappe.throw(_("At most {0} entries per request.").format(MAX_ENTRIES))

	created, errors = [], []
	for index, entry in enumerate(entries):
		savepoint = f"ingest_{index}"
		frappe.db.savepoint(savepoint)
		try:
			values = {k: v for k, v in entry.items() if k in allowed_fields} 
			values.update(extras(entry))
			created.append(frappe.get_doc({"doctype": doctype, **values}).insert().name)
		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			errors.append({"index": index, "error": str(e)})
	return {"created": created, "errors": errors}
