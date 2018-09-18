function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = chooserElement.find('.preview-image img');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.imageChooser,
            onload: IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                imageChosen: function(imageData) {
                    input.val(imageData.id);
                    previewImage.attr({
                        src: imageData.preview.url,
                        width: imageData.preview.width,
                        height: imageData.preview.height,
                        alt: imageData.title,
                        title: imageData.title
                    });
                    chooserElement.removeClass('blank');
                    editLink.attr('href', imageData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
