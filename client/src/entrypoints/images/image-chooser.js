import { Chooser } from '../../components/ChooserWidget';

class ImageChooser extends Chooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;

  initHTMLElements(id) {
    super.initHTMLElements(id);
    this.previewImage = this.chooserElement.querySelector('.preview-image img');
  }

  getStateFromHTML() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no image chosen) or a dict of id, edit_link, title
    and preview (= a dict of url, width, height).
    */
    const state = super.getStateFromHTML();
    if (state) {
      state.title = this.previewImage.getAttribute('alt');
      state.preview = {
        url: this.previewImage.getAttribute('src'),
        width: this.previewImage.getAttribute('width'),
        height: this.previewImage.getAttribute('height'),
      };
    }
    return state;
  }

  renderState(newState) {
    super.renderState(newState);
    this.previewImage.setAttribute('src', newState.preview.url);
    this.previewImage.setAttribute('width', newState.preview.width);
    this.previewImage.setAttribute('alt', newState.title);
    this.previewImage.setAttribute('title', newState.title);
  }
}
window.ImageChooser = ImageChooser;

function createImageChooser(id) {
  /* RemovedInWagtail50Warning */
  return new ImageChooser(id);
}

window.createImageChooser = createImageChooser;
