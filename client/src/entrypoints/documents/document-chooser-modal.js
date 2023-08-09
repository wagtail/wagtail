import $ from 'jquery';
import {
  ChooserModalOnloadHandlerFactory,
  ChooserModal,
} from '../../includes/chooserModal';

class DocumentChooserModalOnloadHandlerFactory extends ChooserModalOnloadHandlerFactory {
  ajaxifyLinks(modal, context) {
    super.ajaxifyLinks(modal, context);

    $('a.upload-one-now').on('click', (event) => {
      // Set current collection ID at upload form tab
      const collectionId = $('#id_collection_id').val();
      if (collectionId) {
        $('#id_document-chooser-upload-collection').val(collectionId);
      }

      event.preventDefault();
    });
  }
}

window.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new DocumentChooserModalOnloadHandlerFactory({
    searchInputDelay: 50,
    creationFormFileFieldSelector: '#id_document-chooser-upload-file',
    creationFormTitleFieldSelector: '#id_document-chooser-upload-title',
    creationFormTabSelector: '#tab-upload',
    creationFormEventName: 'wagtail:documents-upload',
  }).getOnLoadHandlers();

class DocumentChooserModal extends ChooserModal {
  onloadHandlers = window.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS;
}
window.DocumentChooserModal = DocumentChooserModal;
