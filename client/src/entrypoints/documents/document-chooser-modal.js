import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  initPrefillTitleFromFilename,
  SearchController,
} from '../../includes/chooserModal';

function ajaxifyDocumentUploadForm(modal) {
  $('form.document-upload', modal.body).on('submit', function () {
    submitCreationForm(modal, this, { errorContainerSelector: '#tab-upload' });

    return false;
  });

  initPrefillTitleFromFilename(modal, {
    fileFieldSelector: '#id_document-chooser-upload-file',
    titleFieldSelector: '#id_document-chooser-upload-title',
    eventName: 'wagtail:documents-upload',
  });
}

window.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  chooser: function (modal, jsonData) {
    function ajaxifyLinks(context) {
      $('a.document-choice', context).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      $('.pagination a', context).on('click', function () {
        searchController.fetchResults(this.href);
        return false;
      });

      $('a.upload-one-now').on('click', function (e) {
        // Set current collection ID at upload form tab
        const collectionId = $('#collection_chooser_collection_id').val();
        if (collectionId) {
          $('#id_document-chooser-upload-collection').val(collectionId);
        }

        e.preventDefault();
      });

      // Reinitialize tabs to hook up tab event listeners in the modal
      initTabs();
    }

    const searchController = new SearchController({
      form: $('form.document-search', modal.body),
      resultsContainerSelector: '#search-results',
      onLoadResults: (context) => {
        ajaxifyLinks(context);
      },
      inputDelay: 50,
    });
    searchController.attachSearchInput('#id_q');
    searchController.attachSearchFilter('#collection_chooser_collection_id');

    ajaxifyLinks(modal.body);
    ajaxifyDocumentUploadForm(modal);
  },
  document_chosen: function (modal, jsonData) {
    modal.respond('documentChosen', jsonData.result);
    modal.close();
  },
  reshow_upload_form: function (modal, jsonData) {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    initTabs();
    ajaxifyDocumentUploadForm(modal);
  },
};
