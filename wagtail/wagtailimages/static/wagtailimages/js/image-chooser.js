function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = chooserElement.find('.preview-image img');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.image_chooser,
            'responses': {
                'imageChosen': function(imageData) {
                    input.val(imageData.id);
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
