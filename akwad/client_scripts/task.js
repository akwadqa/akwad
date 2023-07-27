frappe.ui.form.on('Task', {
	validate(frm) {
		frm.doc.actual_time = frm.doc.expected_time;
	},
	refresh(frm) {
		frm.add_custom_button(frm.doc.workflow_state).css('background-color', "#FCC50A");
	}
});