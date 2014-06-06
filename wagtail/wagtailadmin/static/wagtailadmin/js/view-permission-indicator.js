$(function() {
    /* Interface to set view permissions from the explorer / editor */
    $('a.action-set-view-permissions').click(function() {
        ModalWorkflow({
            'url': this.href,
            'responses': {
                'setPermission': function(isPublic) {
                    if (isPublic) {
                        $('.view-permission-indicator').removeClass('private').addClass('public');
                    } else {
                        $('.view-permission-indicator').removeClass('public').addClass('private');
                    }
                }
            }
        });
        return false;
    });
});
