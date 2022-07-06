import { ChooserFactory } from '../../components/ChooserWidget';

class SnippetChooserFactory extends ChooserFactory {
  // eslint-disable-next-line no-undef
  widgetClass = SnippetChooser;
}
window.telepath.register(
  'wagtail.snippets.widgets.SnippetChooser',
  SnippetChooserFactory,
);
