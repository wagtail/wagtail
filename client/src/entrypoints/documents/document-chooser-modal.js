import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  initPrefillTitleFromFilename,
  ChooserModalOnloadHandlerFactory,
} from '../../includes/chooserModal';

function ajaxifyDocumentUploadForm(modal) {
  $('form.document-upload', modal.body).on('submit', (event) => {
    submitCreationForm(modal, event.currentTarget, {
      errorContainerSelector: '#tab-upload',
    });

    return false;
  });

  initPrefillTitleFromFilename(modal, {
    fileFieldSelector: '#id_document-chooser-upload-file',
    titleFieldSelector: '#id_document-chooser-upload-title',
    eventName: 'wagtail:documents-upload',
  });
}

class DocumentChooserModalOnloadHandlerFactory extends ChooserModalOnloadHandlerFactory {
  ajaxifyLinks(modal, context) {
    super.ajaxifyLinks(modal, context);

    $('a.upload-one-now').on('click', (event) => {
      // Set current collection ID at upload form tab
      const collectionId = $('#collection_chooser_collection_id').val();
      if (collectionId) {
        $('#id_document-chooser-upload-collection').val(collectionId);
      }

      event.preventDefault();
    });

    // Reinitialize tabs to hook up tab event listeners in the modal
    initTabs();
  }

  onLoadChooseStep(modal, jsonData) {
    super.onLoadChooseStep(modal, jsonData);
    ajaxifyDocumentUploadForm(modal);
  }

  getOnLoadHandlers() {
    const handlers = super.getOnLoadHandlers();
    handlers.reshow_upload_form = (modal, jsonData) => {
      $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
      initTabs();
      ajaxifyDocumentUploadForm(modal);
    };
    return handlers;
  }
}

window.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new DocumentChooserModalOnloadHandlerFactory({
    chooseStepName: 'chooser',
    chosenStepName: 'document_chosen',
    searchFormSelector: 'form.document-search',
    searchFilterSelectors: ['#collection_chooser_collection_id'],
    searchInputDelay: 50,
    chosenResponseName: 'documentChosen',
  }).getOnLoadHandlers();
