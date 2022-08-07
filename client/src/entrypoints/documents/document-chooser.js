import { Chooser } from '../../components/ChooserWidget';
import { removedInWagtail50Warning } from '../../utils/deprecation';

class DocumentChooser extends Chooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS;
}
window.DocumentChooser = DocumentChooser;

function createDocumentChooser(id) {
  removedInWagtail50Warning(
    '`createDocumentChooser(id)` should be replaced with `new DocumentChooser(id)`',
  );
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
