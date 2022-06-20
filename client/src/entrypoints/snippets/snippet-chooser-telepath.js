class SnippetChooserFactory {
  constructor(html, idPattern) {
    this.html = html;
    this.idPattern = idPattern;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    /* the SnippetChooser object also serves as the JS widget representation */
    // eslint-disable-next-line no-undef
    const chooser = new SnippetChooser(id);
    chooser.setState(initialState);
    return chooser;
  }
}
window.telepath.register(
  'wagtail.snippets.widgets.SnippetChooser',
  SnippetChooserFactory,
);
