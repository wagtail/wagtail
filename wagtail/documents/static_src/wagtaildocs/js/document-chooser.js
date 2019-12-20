function createDocumentChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.documentChooser,
            onload: DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                documentChosen: function(docData) {
                    input.val(docData.id);
                    docTitle.text(docData.title);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', docData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
