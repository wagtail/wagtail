import { DocumentChooser } from '../../components/ChooserWidget/DocumentChooserWidget';

window.DocumentChooser = DocumentChooser;

function createDocumentChooser(id) {
  /* RemovedInWagtail50Warning */
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
