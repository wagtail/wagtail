function createSnippetChooser(id, contentType) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': '/admin/snippets/choose/' + contentType + '/', /* TODO: don't hard-code this, as it may be changed in urls.py */
            'responses': {
                'snippetChosen': function(snippetData) {
                    input.val(snippetData.id);
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
