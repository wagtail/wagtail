import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  initPrefillTitleFromFilename,
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
        loadResults(this.href);
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

    var searchForm = $('form.document-search', modal.body);
    var searchUrl = searchForm.attr('action');
    var request;
    function search() {
      loadResults(searchUrl, searchForm.serialize());
      return false;
    }

    function loadResults(url, data) {
      var opts = {
        url: url,
        success: function (resultsData, status) {
          request = null;
          $('#search-results').html(resultsData);
          ajaxifyLinks($('#search-results'));
        },
        error: function () {
          request = null;
        },
      };
      if (data) {
        opts.data = data;
      }
      request = $.ajax(opts);
    }

    ajaxifyLinks(modal.body);
    ajaxifyDocumentUploadForm(modal);

    $('form.document-search', modal.body).on('submit', search);

    $('#id_q').on('input', function () {
      if (request) {
        request.abort();
      }
      clearTimeout($.data(this, 'timer'));
      var wait = setTimeout(search, 50);
      $(this).data('timer', wait);
    });

    $('#collection_chooser_collection_id').on('change', search);
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
