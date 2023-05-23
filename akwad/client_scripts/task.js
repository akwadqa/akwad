frappe.ui.form.on('Task', {
	validate(frm) {
		// your code here
		frm.doc.actual_time = frm.doc.expected_time;
		if (frm.doc.workflow_state === "Completed" || frm.doc.workflow_state === "Cancelled") {
			frm.doc.akd_is_active = 0;
		} else {
			frm.doc.akd_is_active = 1;
		}
	},
	refresh(frm) {
		document.querySelector("#page-Task div[data-fieldtype='Text Editor'] .ql-editor").style.height = "620px";
		document.querySelector("#page-Task div[data-fieldname='akd_test_rsults'] .ql-editor").style.height = "620px";
		frm.add_custom_button(frm.doc.workflow_state).css('background-color', "#FCC50A");
	}
});
