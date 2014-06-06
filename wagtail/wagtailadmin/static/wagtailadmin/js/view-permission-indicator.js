$(function() {
    /* Interface to set view permissions from the explorer / editor */
    $('a.action-set-view-permissions').click(function() {
        ModalWorkflow({
            'url': this.href
        });
        return false;
    });
});
