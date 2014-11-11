function createDocumentChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var editLink = chooserElement.find('.edit-link');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.chooserUrls.documentChooser,
            'responses': {
                'documentChosen': function(docData) {
                    input.val(docData.id);
                    editLink.attr('href', docData.edit_link);
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
