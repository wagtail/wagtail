function createSnippetChooser(id, contentType) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var editLink = chooserElement.find('.edit-link');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.chooserUrls.snippetChooser + contentType + '/',
            'responses': {
                'snippetChosen': function(snippetData) {
                    input.val(snippetData.id);
                    editLink.attr('href', snippetData.edit_link);
                    docTitle.text(snippetData.string);
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
