// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.query_reports["Agreement Review"] = {
	filters: [
		{
			"fieldname": "agreement",
			"label": "Agreement",
			"fieldtype": "Link",
			"options": "Service Agreement",
			"reqd": 1
		},
		{
			"fieldname": "as_of_date",
			"label": "As of Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	],

	onload(report) {
		report.page.add_inner_button(__("Start Renewal"), () => {
			const agreement = frappe.query_report.get_filter_value("agreement");
			if (!agreement) {
				frappe.msgprint(__("Select an agreement first."));
				return;
			}
			frappe.db.get_value("Service Agreement", agreement, ["end_date", "account_owner"]).then((r) => {
				frappe.new_doc("Renewal", {
					agreement,
					due_date: frappe.datetime.add_days(r.message.end_date, -90),
					follow_up_by: r.message.account_owner,
				});
			});
		});
	},

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "flags" && data && data.flags) {
			value = `<span style="color: var(--red-600)">${value}</span>`;
		}
		return value;
	},
};
