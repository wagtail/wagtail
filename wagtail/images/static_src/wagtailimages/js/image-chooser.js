function createImageChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewImage = chooserElement.find('.preview-image img');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    var imageChosenCallback = function(imageData) {
        input.val(imageData.id);
        previewImage.attr({
            src: imageData.preview.url,
            width: imageData.preview.width,
            height: imageData.preview.height,
            alt: imageData.title
        });
        chooserElement.removeClass('blank');
        editLink.attr('href', imageData.edit_link);
    }

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.imageChooser,
            responses: {
                imageChosen: imageChosenCallback
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });

    return imageChosenCallback;
}


//function createBound