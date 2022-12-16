import { Chooser } from '../../components/ChooserWidget';

class DocumentChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = DocumentChooserModal;
}
window.DocumentChooser = DocumentChooser;

function createDocumentChooser(id) {
  /* RemovedInWagtail50Warning */
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
