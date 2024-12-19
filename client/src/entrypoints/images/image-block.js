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
    imageChooserWidget.on('chosen', (data) => {
      altTextField.value = data.default_alt_text;
    });

    return block;
  }
}

window.telepath.register(
  'wagtail.images.blocks.ImageBlock',
  ImageBlockDefinition,
);
