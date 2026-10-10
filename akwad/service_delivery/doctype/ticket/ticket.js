// Copyright (c) 2026, Akwad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Ticket", {
	setup(frm) {
		frm.set_query("agreement", () => ({ filters: { status: ["in", ["Active", "Expiring Soon"]] } }));
		frm.set_query("site", () => ({ filters: { customer: frm.doc.customer } }));
		frm.set_query("raised_by", () => ({
			query: "frappe.contacts.doctype.contact.contact.contact_query",
			filters: { link_doctype: "Customer", link_name: frm.doc.customer },
		}));
	},
});
