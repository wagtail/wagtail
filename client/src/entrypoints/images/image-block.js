class ImageBlockDefinition extends window.wagtailStreamField.blocks
  .StructBlockDefinition {
  render(placeholder, prefix, initialState, initialError) {
    const block = super.render(placeholder, prefix, initialState, initialError);

    const altTextField = document.getElementById(`${prefix}-alt_text`);
    const isDecorativeField = document.getElementById(`${prefix}-decorative`);
    const updateStateInput = () => {
      if (isDecorativeField.checked) {
        altTextField.setAttribute('disabled', true);
      } else {
        altTextField.removeAttribute('disabled');
      }
    };
    updateStateInput();
    isDecorativeField.addEventListener('change', updateStateInput);

    const imageChooserWidget = block.childBlocks.image.widget;
    let lastDefaultAltText = initialState?.image?.default_alt_text || '';
    imageChooserWidget.on('chosen', (data) => {
      /* If the alt text field has not been changed from the previous image's default alt text
      (or the empty string, if there was no previous image), replace it with the new image's
      default alt text */
      if (altTextField.value === lastDefaultAltText) {
        altTextField.value = data.default_alt_text;
      }
      lastDefaultAltText = data.default_alt_text;
    });

    return block;
  }
}

window.telepath.register(
  'wagtail.images.blocks.ImageBlock',
  ImageBlockDefinition,
);
