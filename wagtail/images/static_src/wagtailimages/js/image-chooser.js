function createImageChooser(id) {
    console.log('id: ' + id);
    let chooserElement = $('#' + id + '-chooser');
    let input = $('#' + id);
    let editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        let previewImages = chooserElement.find('.preview-image img');
        ModalWorkflow({
            url: window.chooserUrls.imageChooser,
            onload: IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                imageChosen: function(imageData) {
                    input.val(imageData.id);
                    previewImages.each( 
                        function(){
                            $( this ).attr({
                                src: imageData.preview.url,
                                width: imageData.preview.width,
                                height: imageData.preview.height,
                                alt: imageData.title,
                                "data-original-width": imageData.preview.original_width,
                                "data-original-height": imageData.preview.original_height
                            })
                        }
                        )
                    chooserElement.removeClass('blank');
                    editLink.attr('href', imageData.edit_link);
                    let areaChooser = $('div.select-area-chooser', chooserElement);
                    if(areaChooser.length){
                        window.runJcrop(areaChooser, 'remove');//need to completely rebuild the associated jcrop instance if changing the image
                    }
                    
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
