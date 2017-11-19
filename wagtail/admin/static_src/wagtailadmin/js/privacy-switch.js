$(function() {
    /* Interface to set permissions from the explorer / editor */
    $('a.action-set-privacy').click(function() {
        ModalWorkflow({
            url: this.href,
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
