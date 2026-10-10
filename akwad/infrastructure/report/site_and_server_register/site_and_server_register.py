# Copyright (c) 2026, Akwad and contributors
# For license information, please see license.txt

import frappe

from akwad.report_utils import col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		col("Customer", "customer", "Link", "Customer", 150),
		col("Site", "site", "Link", "Site", 100),
		col("Site Name", "site_name", width=150),
		col("Status", "status", width=100),
		col("Platform", "application_platform", width=110),
		col("Version", "platform_version", width=80),
		col("Domain", "domain", width=150),
		col("Domain Expiry", "domain_expiry", "Date", width=110),
		col("Environment", "environment", width=100),
		col("URL", "url", "Data", width=220),
		col("Available", "available", "Check", width=80),
		col("Server", "server", "Link", "Server", 130),
		col("Server IP", "server_ip", width=110),
		col("Provider", "hosting_provider", "Link", "Hosting Provider", 120),
		col("Region", "region", width=100),
		col("Instance Type", "instance_type", width=110),
	]


def get_data(filters):
	conditions, values = [], {}
	for key, column in (
		("customer", "s.customer"),
		("status", "s.status"),
		("application_platform", "s.application_platform"),
		("environment", "s.environment"),
		("hosting_provider", "srv.hosting_provider"),
	):
		if filters.get(key):
			conditions.append(f"and {column} = %({key})s")
			values[key] = filters[key]

	return frappe.db.sql(
		f"""
		select s.customer, s.name as site, s.site_name, s.status, s.application_platform, s.platform_version,
			s.domain, s.domain_expiry, s.environment, s.url, s.available, s.server,
			srv.server_ip, srv.hosting_provider, srv.region, srv.instance_type
		from `tabSite` s
		left join `tabServer` srv on srv.name = s.server
		where 1 = 1 {" ".join(conditions)}
		order by s.customer, s.name
		""",
		values,
		as_dict=True,
	)
