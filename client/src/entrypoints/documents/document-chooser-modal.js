import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import { ChooserModalOnloadHandlerFactory } from '../../includes/chooserModal';

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

  onLoadReshowCreationFormStep(modal, jsonData) {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    initTabs();
    this.ajaxifyCreationForm(modal);
  }

  getOnLoadHandlers() {
    const handlers = super.getOnLoadHandlers();
    handlers.reshow_upload_form = (modal, jsonData) => {
      this.onLoadReshowCreationFormStep(modal, jsonData);
    };
    return handlers;
  }
}

window.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new DocumentChooserModalOnloadHandlerFactory({
    searchFilterSelectors: ['#collection_chooser_collection_id'],
    searchInputDelay: 50,
    chosenResponseName: 'documentChosen',
    creationFormSelector: 'form.document-upload',
    creationFormErrorContainerSelector: '#tab-upload',
    creationFormFileFieldSelector: '#id_document-chooser-upload-file',
    creationFormTitleFieldSelector: '#id_document-chooser-upload-title',
    creationFormEventName: 'wagtail:documents-upload',
  }).getOnLoadHandlers();
