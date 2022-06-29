import $ from 'jquery';

class ImageChooser {
  constructor(id) {
    this.chooserElement = $('#' + id + '-chooser');
    this.previewImage = this.chooserElement.find('.preview-image img');
    this.input = $('#' + id);
    this.editLink = this.chooserElement.find('.edit-link');
    this.chooserBaseUrl = this.chooserElement.data('chooserUrl');

    this.state = this.getStateFromHTML();

    /* hook up chooser API to the buttons */
    $('.action-choose', this.chooserElement).on('click', () => {
      this.openChooserModal();
    });

    $('.action-clear', this.chooserElement).on('click', () => {
      this.clear();
    });
  }

  getStateFromHTML() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no image chosen) or a dict of id, edit_link, title
    and preview (= a dict of url, width, height).

    The result returned from the image chooser modal (see get_image_result_data in
    wagtail.images.views.chooser) is a superset of this, and can therefore be passed directly to
    chooser.setState.
    */
    if (this.input.val()) {
      return {
        id: this.input.val(),
        edit_link: this.editLink.attr('href'),
        title: this.previewImage.attr('alt'),
        preview: {
          url: this.previewImage.attr('src'),
          width: this.previewImage.attr('width'),
          height: this.previewImage.attr('height'),
        },
      };
    } else {
      return null;
    }
  }

  getState() {
    return this.state;
  }

  getValue() {
    return this.state && this.state.id;
  }

  setState(newState) {
    this.state = newState;
    if (newState) {
      this.renderState(newState);
    } else {
      this.renderEmptyState();
    }
  }

  clear() {
    this.setState(null);
  }

  renderEmptyState() {
    this.input.val('');
    this.chooserElement.addClass('blank');
  }

  renderState(newState) {
    this.input.val(newState.id);
    this.previewImage.attr({
      src: newState.preview.url,
      width: newState.preview.width,
      height: newState.preview.height,
      alt: newState.title,
      title: newState.title,
    });
    this.chooserElement.removeClass('blank');
    this.editLink.attr('href', newState.edit_link);
  }

  getTextLabel(opts) {
    if (!this.state) return null;
    const result = this.state.title;
    if (opts && opts.maxLength && result.length > opts.maxLength) {
      return result.substring(0, opts.maxLength - 1) + '…';
    }
    return result;
  }

  focus() {
    $('.action-choose', this.chooserElement).focus();
  }

  getModalUrl() {
    return this.chooserBaseUrl;
  }

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.getModalUrl(),
      // eslint-disable-next-line no-undef
      onload: IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        imageChosen: (result) => {
          this.setState(result);
        },
      },
    });
  }
}

function createImageChooser(id) {
  return new ImageChooser(id);
}

window.createImageChooser = createImageChooser;
