import { Chooser } from '../../components/ChooserWidget';

/* global wagtailConfig */

class SnippetChooser extends Chooser {
  titleStateKey = 'string';

  getModalUrl() {
    let urlQuery = '';
    if (wagtailConfig.ACTIVE_CONTENT_LOCALE) {
      // The user is editing a piece of translated content.
      // Pass the locale along as a request parameter. If this
      // snippet is also translatable, the results will be
      // pre-filtered by this locale.
      urlQuery = '?locale=' + wagtailConfig.ACTIVE_CONTENT_LOCALE;
    }
    return this.chooserBaseUrl + urlQuery;
  }
}
window.SnippetChooser = SnippetChooser;

function createSnippetChooser(id) {
  /* RemovedInWagtail50Warning */
  return new SnippetChooser(id);
}
window.createSnippetChooser = createSnippetChooser;
