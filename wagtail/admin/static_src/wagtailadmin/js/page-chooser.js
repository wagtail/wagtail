function createPageChooser(id, pageTypes, openAtParentId, canChooseRoot, userPerms) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        var initialUrl = chooserElement.data('chooserUrl');
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
            onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                pageChosen: function(pageData) {
                    input.val(pageData.id);
                    openAtParentId = pageData.parentId;
                    pageTitle.text(pageData.adminTitle);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', pageData.editUrl);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        openAtParentId = null;
        chooserElement.addClass('blank');
    });
}
