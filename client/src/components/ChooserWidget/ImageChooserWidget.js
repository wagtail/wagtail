/* global ImageChooserModal */

import { Chooser, ChooserFactory } from '.';

export class ImageChooser extends Chooser {
  chooserModalClass = ImageChooserModal;

  initHTMLElements(id) {
    super.initHTMLElements(id);
    this.previewImage = this.chooserElement.querySelector(
      '[data-chooser-image]',
    );
  }

  /**
   * Constructs the initial state of the chooser from the rendered (static) HTML.
   * The state is either null (no image chosen) or an object containing the image details.
   *
   * @returns {Object|null} The initial state of the chooser. If an image is chosen,
   * the state object contains the following properties:
   * - id: {number} The ID of the chosen image.
   * - edit_url: {string} The URL to edit the chosen image.
   * - title: {string} The title of the chosen image.
   * - preview: {Object} An object containing the preview details of the chosen image:
   *   - url: {string} The URL of the preview image.
   *   - width: {string} The width of the preview image.
   *   - height: {string} The height of the preview image.
   */
  getStateFromHTML() {
    const state = super.getStateFromHTML();
    if (state) {
      state.preview = {
        url: this.previewImage.getAttribute('src'),
        width: this.previewImage.getAttribute('width'),
        height: this.previewImage.getAttribute('height'),
      };
      state.default_alt_text = this.previewImage.getAttribute(
        'data-default-alt-text',
      );
    }
    return state;
  }

  renderState(newState) {
    super.renderState(newState);
    this.previewImage.setAttribute('src', newState.preview.url);
    this.previewImage.setAttribute('width', newState.preview.width);
    this.previewImage.setAttribute(
      'data-default-alt-text',
      newState.default_alt_text,
    );
  }
}

export class ImageChooserFactory extends ChooserFactory {
  widgetClass = ImageChooser;
  chooserModalClass = ImageChooserModal;
}
