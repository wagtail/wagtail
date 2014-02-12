function createPageChooser(id, pageType, openAtParentId) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        var initialUrl = window.page_chooser;
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