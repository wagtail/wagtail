$(function() {
    /* Interface to view the workflow status from the explorer / editor */
    $('button.action-workflow-status').on('click', function() {
        ModalWorkflow({
            url: this.getAttribute('data-url'),
        });
        return false;
    });
});
