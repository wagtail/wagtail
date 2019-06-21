$(function() {
    /* Interface to set permissions from the explorer / editor */
    $('button.action-set-privacy').on('click', function() {
        ModalWorkflow({
            url: this.getAttribute('data-url'),
            onload: {
                'set_privacy': function(modal, jsonData) {
                    $('form', modal.body).on('submit', function() {
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

                    $("input[name='restriction_type']", modal.body).on('change', refreshFormFields);
                },
                'set_privacy_done': function(modal, jsonData) {
                    modal.respond('setPermission', jsonData['is_public']);
                    modal.close();
                }
            },
            responses: {
                setPermission: function(isPublic) {
                    if (isPublic) {
                        $('.privacy-indicator').removeClass('private').addClass('public');
                    } else {
                        $('.privacy-indicator').removeClass('public').addClass('private');
                    }
                }
            }
        });
        return false;
    });
});
