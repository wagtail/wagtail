function createPageChooser(id, pageTypes, openAtParentId, canChooseRoot, userPerms) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).click(function() {
        var initialUrl = window.chooserUrls.pageChooser;
        if (openAtParentId) {
            initialUrl += openAtParentId + '/';
        }

        var urlParams = {page_type: pageTypes.join(',')};
        if (canChooseRoot) {
            urlParams.can_choose_root = 'true';
        }
        if (userPerms) {
            urlParams.user_perms = userPerms;
        }

        ModalWorkflow({
            url: initialUrl,
            urlParams: urlParams,
            responses: {
                pageChosen: function(pageData) {
                    input.val(pageData.id);
                    openAtParentId = pageData.parentId;
                    pageTitle.text(pageData.title);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', pageData.editUrl);
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
