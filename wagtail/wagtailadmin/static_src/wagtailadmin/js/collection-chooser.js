function createCollectionChooser(id, openAtParentId, canChooseRoot) {
    var chooserElement = $('#' + id + '-chooser');
    var collectionTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).click(function() {
        var initialUrl = window.chooserUrls.collectionChooser;
        if (openAtParentId) {
            initialUrl += openAtParentId + '/';
        }

        var urlParams = {modal: 'true'};
        if (canChooseRoot) {
            urlParams.can_choose_root = 'true';
        }

        ModalWorkflow({
            url: initialUrl,
            urlParams: urlParams,
            responses: {
                collectionChosen: function(collectionData) {
                    input.val(collectionData.id);
                    input.trigger('change');
                    openAtParentId = collectionData.parentId;
                    collectionTitle.text(collectionData.name);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', collectionData.editUrl);
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        input.trigger('change');
        openAtParentId = null;
        chooserElement.addClass('blank');
    });
}
