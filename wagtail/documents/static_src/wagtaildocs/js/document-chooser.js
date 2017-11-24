function createDocumentChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            url: window.chooserUrls.documentChooser,
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

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
