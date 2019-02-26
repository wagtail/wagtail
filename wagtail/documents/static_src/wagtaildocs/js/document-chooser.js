function createDocumentChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    function documentChosen(docData, initial) {
        if (!initial) {
            input.val(docData.id);
        }
        docTitle.text(docData.title);
        chooserElement.removeClass('blank');
        editLink.attr('href', docData.edit_link);
    }

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.documentChooser,
            onload: DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                documentChosen: documentChosen,
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });

    if (input.val()) {
        $.ajax(window.chooserUrls.documentChooser + encodeURIComponent(input.val()) + '/')
            .done(function (data) {
                documentChosen(data.result, true);
            });
    }
}
