import { Chooser, ChooserFactory } from '.';

export class ImageChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = ImageChooserModal;

  initHTMLElements(id) {
    super.initHTMLElements(id);
    this.previewImage = this.chooserElement.querySelector(
      '[data-chooser-image]',
    );
  }

  getStateFromHTML() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no image chosen) or a dict of id, edit_url, title
    and preview (= a dict of url, width, height).
    */
    const state = super.getStateFromHTML();
    if (state) {
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
  }
}

export class ImageChooserFactory extends ChooserFactory {
  widgetClass = ImageChooser;
  // eslint-disable-next-line no-undef
  chooserModalClass = ImageChooserModal;
}
