function(modal) {
    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });

    var restrictionTypePasswordField = $("input[name='restriction_type'][value='password']", modal.body);
    var passwordField = $("#id_password", modal.body);
    function refreshFormFields() {
        if (restrictionTypePasswordField.is(':checked')) {
            passwordField.removeAttr('disabled');
        } else {
            passwordField.attr('disabled', true);
        }
    }
    refreshFormFields();

    $("input[name='restriction_type']", modal.body).change(refreshFormFields);
}
