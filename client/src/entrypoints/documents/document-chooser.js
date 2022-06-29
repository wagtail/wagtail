import { Chooser } from '../../components/ChooserWidget';

class DocumentChooser extends Chooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS;
  chosenResponseName = 'documentChosen';
}

function createDocumentChooser(id) {
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
