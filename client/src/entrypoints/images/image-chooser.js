import $ from 'jquery';

function createImageChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const previewImage = chooserElement.find('.preview-image img');
  const input = $('#' + id);
  const editLink = chooserElement.find('.edit-link');
  const chooserBaseUrl = chooserElement.data('chooserUrl');

  /*
  Construct initial state of the chooser from the rendered (static) HTML and arguments passed to
  createImageChooser. State is either null (= no image chosen) or a dict of id, edit_link,
  title and preview (= a dict of url, width, height).

  The result returned from the image chooser modal (see get_image_result_data in
  wagtail.images.views.chooser) is a superset of this, and can therefore be passed directly to
  chooser.setState.
  */
  let state = null;
  if (input.val()) {
    state = {
      id: input.val(),
      edit_link: editLink.attr('href'),
      title: previewImage.attr('alt'),
      preview: {
        url: previewImage.attr('src'),
        width: previewImage.attr('width'),
        height: previewImage.attr('height'),
      },
    };
  }

  /* define public API functions for the chooser */
  const chooser = {
    getState: () => state,
    getValue: () => state && state.id,
    setState: (newState) => {
      if (newState) {
        input.val(newState.id);
        previewImage.attr({
          src: newState.preview.url,
          width: newState.preview.width,
          height: newState.preview.height,
          alt: newState.title,
          title: newState.title,
        });
        chooserElement.removeClass('blank');
        editLink.attr('href', newState.edit_link);
      } else {
        input.val('');
        chooserElement.addClass('blank');
      }

      state = newState;
    },
    getTextLabel: (opts) => {
      if (!state) return null;
      const result = state.title;
      if (opts && opts.maxLength && result.length > opts.maxLength) {
        return result.substring(0, opts.maxLength - 1) + '…';
      }
      return result;
    },
    focus: () => {
      $('.action-choose', chooserElement).focus();
    },

    openChooserModal: () => {
      // eslint-disable-next-line no-undef
      ModalWorkflow({
        url: chooserBaseUrl,
        // eslint-disable-next-line no-undef
        onload: IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          imageChosen: (result) => {
            chooser.setState(result);
          },
        },
      });
    },

    clear: () => {
      chooser.setState(null);
    },
  };

  /* hook up chooser API to the buttons */
  $('.action-choose', chooserElement).on('click', () => {
    chooser.openChooserModal();
  });

  $('.action-clear', chooserElement).on('click', () => {
    chooser.clear();
  });

  return chooser;
}

window.createImageChooser = createImageChooser;
