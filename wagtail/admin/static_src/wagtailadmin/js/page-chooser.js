function createPageChooser(id, pageTypes, openAtParentId, canChooseRoot, userPerms) {
    var chooserElement = $('#' + id + '-chooser');
    var pageTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    function pageChosen(pageData, initial) {
        if (!initial) {
            input.val(pageData.id);
        }
        openAtParentId = pageData.parentId;
        pageTitle.text(pageData.title);
        chooserElement.removeClass('blank');
        editLink.attr('href', pageData.editUrl);
    }

    $('.action-choose', chooserElement).on('click', function() {
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
            onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                pageChosen: pageChosen,
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        openAtParentId = null;
        chooserElement.addClass('blank');
    });

    if (input.val()) {
        $.ajax({
            url: window.wagtailConfig.ADMIN_API.PAGES + encodeURIComponent(input.val()) + '/',
        }).done(function (data) {
            pageChosen({
                id: data.id,
                title: data.admin_display_title,
                parentId: (data.meta.parent && data.meta.parent.id) ? data.meta.parent.id : null,
                editUrl: window.wagtailConfig.ADMIN_URLS.PAGES
                         + data.id + '/edit/'}, true);
        });
    }
}
