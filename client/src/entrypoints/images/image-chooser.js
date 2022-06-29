class ImageChooser {
  constructor(id) {
    this.chooserElement = document.getElementById(`${id}-chooser`);
    this.previewImage = this.chooserElement.querySelector('.preview-image img');
    this.input = document.getElementById(id);
    this.editLink = this.chooserElement.querySelector('.edit-link');
    this.chooserBaseUrl = this.chooserElement.dataset.chooserUrl;

    this.state = this.getStateFromHTML();

    /* hook up chooser API to the buttons */
    for (const btn of this.chooserElement.querySelectorAll('.action-choose')) {
      btn.addEventListener('click', () => {
        this.openChooserModal();
      });
    }
    for (const btn of this.chooserElement.querySelectorAll('.action-clear')) {
      btn.addEventListener('click', () => {
        this.clear();
      });
    }
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
    if (this.input.value) {
      return {
        id: this.input.value,
        edit_link: this.editLink.getAttribute('href'),
        title: this.previewImage.getAttribute('alt'),
        preview: {
          url: this.previewImage.getAttribute('src'),
          width: this.previewImage.getAttribute('width'),
          height: this.previewImage.getAttribute('height'),
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
    this.input.setAttribute('value', '');
    this.chooserElement.classList.add('blank');
  }

  renderState(newState) {
    this.input.setAttribute('value', newState.id);
    this.previewImage.setAttribute('src', newState.preview.url);
    this.previewImage.setAttribute('width', newState.preview.width);
    this.previewImage.setAttribute('alt', newState.title);
    this.previewImage.setAttribute('title', newState.title);
    this.chooserElement.classList.remove('blank');
    this.editLink.setAttribute('href', newState.edit_link);
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
    this.chooserElement.querySelector('.action-choose').focus();
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
