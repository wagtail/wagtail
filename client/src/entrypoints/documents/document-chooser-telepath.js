import { ChooserFactory } from '../../components/ChooserWidget';

class DocumentChooserFactory extends ChooserFactory {
  // eslint-disable-next-line no-undef
  widgetClass = DocumentChooser;
}
window.telepath.register(
  'wagtail.documents.widgets.DocumentChooser',
  DocumentChooserFactory,
);
