function createSnippetChooser(id, modelString) {
    var chooserElement = $('#' + id + '-chooser');
    var docTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        var urlQuery = '';
        if (wagtailConfig.ACTIVE_CONTENT_LOCALE) {
            // The user is editing a piece of translated content.
            // Pass the locale along as a request parameter. If this
            // snippet is also translatable, the results will be
            // pre-filtered by this locale.
            urlQuery = '?locale=' + wagtailConfig.ACTIVE_CONTENT_LOCALE;
        }

        ModalWorkflow({
            url: chooserElement.data('chooserUrl') + modelString + '/' + urlQuery,
            onload: SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                snippetChosen: function(snippetData) {
                    input.val(snippetData.id);
                    docTitle.text(snippetData.string);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', snippetData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
