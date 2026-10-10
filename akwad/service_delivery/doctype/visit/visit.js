// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visit", {
	setup(frm) {
		frm.set_query("agreement", () => ({ filters: { status: ["in", ["Active", "Expiring Soon"]] } }));
		frm.set_query("site", () => ({ filters: { customer: frm.doc.customer } }));
	},

	// the purpose decides the default; the visit can still override it
	purpose(frm) {
		if (frm.doc.purpose) {
			frm.set_value("counts_against_allowance", frm.doc.purpose === "Complimentary" ? 0 : 1);
		}
	},
});
