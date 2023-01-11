import { Chooser, ChooserFactory } from '../../components/ChooserWidget';

class DocumentChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = DocumentChooserModal;
}
window.DocumentChooser = DocumentChooser;

class DocumentChooserFactory extends ChooserFactory {
  widgetClass = DocumentChooser;
}
window.DocumentChooserFactory = DocumentChooserFactory;

function createDocumentChooser(id) {
  /* RemovedInWagtail50Warning */
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
