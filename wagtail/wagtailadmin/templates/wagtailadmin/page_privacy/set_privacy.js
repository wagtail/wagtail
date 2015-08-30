function(modal) {
    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });

    var restrictionTypePasswordField = $("input[name='restriction_type'][value='password']", modal.body),
        restrictionTypeUsersGroups = $("input[name='restriction_type'][value='users_groups']", modal.body),
        passwordField = $(".password-field", modal.body),
        usersGroupsFields = $('#users-groups-fields', modal.body);

    function refreshFormFields() {
        if (restrictionTypePasswordField.is(':checked')) {
            passwordField.show();
            usersGroupsFields.hide();
        } else if (restrictionTypeUsersGroups.is(':checked')){
            passwordField.hide();
            usersGroupsFields.show();
        } else {
            passwordField.hide();
            usersGroupsFields.hide();
        }
    }
    refreshFormFields();

    $("input[name='restriction_type']", modal.body).change(refreshFormFields);
}
