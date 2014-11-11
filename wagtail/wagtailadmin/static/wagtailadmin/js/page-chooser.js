function createPageChooser(id, pageType, openAtParentId) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var editLink = chooserElement.find('.edit-link');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        var initialUrl = window.chooserUrls.pageChooser;
        if (openAtParentId) {
            initialUrl += openAtParentId + '/';
        }
        ModalWorkflow({
            'url': initialUrl,
            'urlParams': {'page_type': pageType},
            'responses': {
                'pageChosen': function(pageData) {
                    input.val(pageData.id);
                    openAtParentId = pageData.parentId;
                    pageTitle.text(pageData.title);
                    editLink.attr('href', pageData.editUrl);
                    chooserElement.removeClass('blank');
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        openAtParentId = null;
        chooserElement.addClass('blank');
    });
}
