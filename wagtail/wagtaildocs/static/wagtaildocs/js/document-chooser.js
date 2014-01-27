function createDocumentChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': '/admin/documents/chooser/', /* TODO: don't hard-code this, as it may be changed in urls.py */
            'responses': {
                'documentChosen': function(docData) {
                    input.val(docData.id);
                    docTitle.text(docData.title);
                    chooserElement.removeClass('blank');
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
