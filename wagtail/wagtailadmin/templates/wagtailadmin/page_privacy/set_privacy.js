function(modal) {
    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });

    var restrictionTypePasswordField = $("input[name='restriction_type'][value='password']", modal.body);
    var restrictionTypeGroupsField = $("input[name='restriction_type'][value='groups']", modal.body);
    var passwordField = $(".password-field", modal.body);
    var groupsFields = $('#groups-fields', modal.body);

    function refreshFormFields() {
        if (restrictionTypePasswordField.is(':checked')) {
            passwordField.show();
            groupsFields.hide();
        } else if (restrictionTypeGroupsField.is(':checked')){
            passwordField.hide();
            groupsFields.show();
        } else {
            passwordField.hide();
            groupsFields.hide();
        }
    }
    refreshFormFields();

    $("input[name='restriction_type']", modal.body).change(refreshFormFields);
}
