function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = chooserElement.find('.preview-image img');
    var editLink = chooserElement.find('.edit-link');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.chooserUrls.imageChooser,
            'responses': {
                'imageChosen': function(imageData) {
                    input.val(imageData.id);
                    editLink.attr('href', imageData.edit_link);
                    previewImage.attr({
                        'src': imageData.preview.url,
                        'width': imageData.preview.width,
                        'height': imageData.preview.height,
                        'alt': imageData.title
                    });
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
