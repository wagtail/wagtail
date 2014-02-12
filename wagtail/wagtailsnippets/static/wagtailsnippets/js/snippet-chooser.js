function createSnippetChooser(id, contentType) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.snippet_chooser + contentType + '/',  
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
