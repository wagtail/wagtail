class ImageChooserFactory {
  constructor(html, idPattern) {
    this.html = html;
    this.idPattern = idPattern;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    /* the ImageChooser object also serves as the JS widget representation */
    // eslint-disable-next-line no-undef
    const chooser = new ImageChooser(id);
    chooser.setState(initialState);
    return chooser;
  }
}
window.telepath.register(
  'wagtail.images.widgets.ImageChooser',
  ImageChooserFactory,
);
