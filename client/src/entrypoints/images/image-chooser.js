import $ from 'jquery';

function createImageChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const previewImage = chooserElement.find('.preview-image img');
  const input = $('#' + id);
  const editLink = chooserElement.find('.edit-link');

  $('.action-choose', chooserElement).on('click', () => {
    // eslint-disable-next-line no-undef, new-cap
    ModalWorkflow({
      url: chooserElement.data('chooserUrl'),
      // eslint-disable-next-line no-undef
      onload: IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        imageChosen: (imageData) => {
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

  $('.action-clear', chooserElement).on('click', () => {
    input.val('');
    chooserElement.addClass('blank');
  });
}
window.createImageChooser = createImageChooser;
