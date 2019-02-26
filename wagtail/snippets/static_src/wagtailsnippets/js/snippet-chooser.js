function createSnippetChooser(id, modelString) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    function snippetChosen(snippetData, initial) {
        if (!initial) {
            input.val(snippetData.id);
        }
        docTitle.text(snippetData.string);
        chooserElement.removeClass('blank');
        editLink.attr('href', snippetData.edit_link);
    }

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.snippetChooser + modelString + '/',
            onload: SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                snippetChosen: snippetChosen,
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });

    if (input.val()) {
        $.ajax(window.chooserUrls.snippetChooser + modelString + '/'
               + encodeURIComponent(input.val()) + '/')
            .done(function (data) {
                snippetChosen(data.result, true);
            });
    }
}
