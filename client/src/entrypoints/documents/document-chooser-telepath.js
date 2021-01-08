class DocumentChooser {
  constructor(html, idForLabel) {
    this.html = html;
    this.idForLabel = idForLabel;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    /* the chooser object returned by createDocumentChooser also serves as the JS widget representation */
    // eslint-disable-next-line no-undef
    const chooser = createDocumentChooser(id);
    chooser.setState(initialState);
  }
}
window.telepath.register('wagtail.documents.widgets.DocumentChooser', DocumentChooser);
