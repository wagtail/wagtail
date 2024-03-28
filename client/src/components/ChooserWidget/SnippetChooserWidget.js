import { ChooserModal } from '../../includes/chooserModal';
import { Chooser, ChooserFactory } from '.';
import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';

class SnippetChooserModal extends ChooserModal {
  getURLParams(opts) {
    const params = super.getURLParams(opts);
    if (WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE) {
      // The user is editing a piece of translated content.
      // Pass the locale along as a request parameter. If this
      // snippet is also translatable, the results will be
      // pre-filtered by this locale.
      params.locale = WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE;
    }
    return params;
  }
}

export class SnippetChooser extends Chooser {
  titleStateKey = 'string';
  chooserModalClass = SnippetChooserModal;
}

export class SnippetChooserFactory extends ChooserFactory {
  widgetClass = SnippetChooser;
  chooserModalClass = SnippetChooserModal;
}
