class DocumentChooserFactory {
  constructor(html, idPattern) {
    this.html = html;
    this.idPattern = idPattern;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    /* the DocumentChooser object also serves as the JS widget representation */
    // eslint-disable-next-line no-undef
    const chooser = new DocumentChooser(id);
    chooser.setState(initialState);
    return chooser;
  }
}
window.telepath.register(
  'wagtail.documents.widgets.DocumentChooser',
  DocumentChooserFactory,
);
