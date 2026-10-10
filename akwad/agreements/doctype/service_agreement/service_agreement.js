// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

// Fields each plan template fills on Service Agreement when picked.
const HOSTING_PLAN_FIELDS = ["storage_gb", "bandwidth_gb", "backup_storage_gb"];
const SUPPORT_PLAN_FIELDS = ["support_hours", "support_hours_window", "visits_per_month"];

frappe.ui.form.on("Service Agreement", {
	setup(frm) {
		frm.set_query("project", () => ({ filters: { customer: frm.doc.customer } }));
		frm.set_query("hosting_plan", () => ({ filters: { disabled: 0 } }));
		frm.set_query("support_plan", () => ({ filters: { disabled: 0 } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Create Site"), () =>
			frappe.new_doc("Site", { customer: frm.doc.customer })
		);

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Activate"), () =>
				frm.call("activate").then(() => frm.reload_doc())
			).addClass("btn-primary");
		}

		if (["Active", "Expiring Soon", "Expired"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Start Renewal"), () =>
				frappe.new_doc("Renewal", {
					agreement: frm.doc.name,
					due_date: frappe.datetime.add_days(frm.doc.end_date, -90),
					follow_up_by: frm.doc.account_owner,
				})
			);
		}

		if (frm.doc.status !== "Draft") {
			frm.add_custom_button(
				__("Agreement Review"),
				() => frappe.set_route("query-report", "Agreement Review", { agreement: frm.doc.name }),
				__("Actions")
			);
		}

		if (["Active", "Expiring Soon", "Expired"].includes(frm.doc.status)) {
			frm.add_custom_button(
				__("Generate Usage Summary"),
				() => {
					frappe.prompt(
						{
							fieldname: "month",
							fieldtype: "Data",
							label: __("Month (YYYY-MM)"),
							description: __("Blank for last month. A month is generated once and never regenerated."),
						},
						(values) =>
							frm
								.call("generate_usage_summary", { month: values.month })
								.then((r) => frappe.set_route("Form", "Usage Summary", r.message)),
						__("Generate Usage Summary")
					);
				},
				__("Actions")
			);
			frm.add_custom_button(
				__("Cancel Agreement"),
				() =>
					frappe.prompt(
						{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason") },
						(values) =>
							frm.call("cancel_agreement", { reason: values.reason }).then(() => frm.reload_doc()),
						__("Cancel Agreement")
					),
				__("Actions")
			);
		}
	},

	agreement_type: (frm) => frm.trigger("set_warranty_end_date"),
	start_date: (frm) => frm.trigger("set_warranty_end_date"),
	warranty_months: (frm) => frm.trigger("set_warranty_end_date"),

	// Plans are Templates -> Fill fields
	hosting_plan(frm) {
		if (!frm.doc.hosting_plan) return;
		frappe.db.get_doc("Hosting Plan", frm.doc.hosting_plan).then((plan) => {
			HOSTING_PLAN_FIELDS.forEach((fieldname) => frm.set_value(fieldname, plan[fieldname]));
		});
	},

	support_plan(frm) {
		if (!frm.doc.support_plan) return;
		frappe.db.get_doc("Support Plan", frm.doc.support_plan).then((plan) => {
			SUPPORT_PLAN_FIELDS.forEach((fieldname) => frm.set_value(fieldname, plan[fieldname]));

			frm.clear_table("sla_resolution");
			(plan.sla_resolution || []).forEach((row) => {
				const child = frm.add_child("sla_resolution");
				child.priority = row.priority;
				child.response_time = row.response_time;
				child.resolution_time = row.resolution_time;
			});
			frm.refresh_field("sla_resolution");
		});
	},

	// mirrors the server rule: end = start + warranty months - 1 day
	set_warranty_end_date(frm) {
		const { agreement_type, start_date, warranty_months } = frm.doc;
		if (agreement_type !== "Warranty" || !start_date || !warranty_months) return;
		frm.set_value(
			"end_date",
			frappe.datetime.add_days(frappe.datetime.add_months(start_date, warranty_months), -1)
		);
	},
});
