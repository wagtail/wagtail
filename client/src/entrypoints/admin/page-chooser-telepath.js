class PageChooserFactory {
  constructor(html, idPattern, config) {
    this.html = html;
    this.idPattern = idPattern;
    this.config = config;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    /* the PageChooser object also serves as the JS widget representation */
    // eslint-disable-next-line no-undef
    const chooser = new PageChooser(id, this.config);
    chooser.setState(initialState);
    return chooser;
  }
}
window.telepath.register('wagtail.widgets.PageChooser', PageChooserFactory);
