// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Site", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status !== "Active") return;

		frm.add_custom_button(__("Create Backup Job"), () =>
			frappe.new_doc("Backup Job", {
				site: frm.doc.name,
				server: frm.doc.server,
				scope: "Application",
			})
		);
	},
});
