/* global ImageChooserModal */

import { Chooser, ChooserFactory } from '.';

/**
 * @typedef {object} ImageChosenState A state object representing the chosen image.
 * @property {number} id The ID of the chosen image.
 * @property {string} edit_url The URL to edit the chosen image.
 * @property {string} title The title of the chosen image.
 * @property {object} preview Preview details of the chosen image.
 * @property {string} preview.url The URL of the preview image.
 * @property {string} preview.width The width of the preview image.
 * @property {string} preview.height The height of the preview image.
 * @property {string} default_alt_text The default alt text for the image.
 */

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
   * @returns {ImageChosenState|null} The initial state of the chooser or null if no image is chosen.
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
