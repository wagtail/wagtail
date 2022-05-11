import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  initPrefillTitleFromFilename,
  SearchController,
} from '../../includes/chooserModal';

function ajaxifyImageUploadForm(modal) {
  $('form.image-upload', modal.body).on('submit', function () {
    if (!$('#id_image-chooser-upload-title', modal.body).val()) {
      var li = $('#id_image-chooser-upload-title', modal.body).closest('li');
      if (!li.hasClass('error')) {
        li.addClass('error');
        $('#id_image-chooser-upload-title', modal.body)
          .closest('.field-content')
          .append(
            '<p class="error-message"><span>This field is required.</span></p>',
          );
      }
      setTimeout(cancelSpinner, 500);
    } else {
      submitCreationForm(modal, this, {
        errorContainerSelector: '#tab-upload',
      });
    }

    return false;
  });

  initPrefillTitleFromFilename(modal, {
    fileFieldSelector: '#id_image-chooser-upload-file',
    titleFieldSelector: '#id_image-chooser-upload-title',
    eventName: 'wagtail:images-upload',
  });
}

window.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  chooser: function (modal, jsonData) {
    function ajaxifyLinks(context) {
      $('.listing a', context).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      $('.pagination a', context).on('click', function () {
        searchController.fetchResults(this.href);
        return false;
      });
    }

    const searchController = new SearchController({
      form: $('form.image-search', modal.body),
      resultsContainerSelector: '#image-results',
      onLoadResults: (context) => {
        ajaxifyLinks(context);
      },
    });
    searchController.attachSearchInput('#id_q');
    searchController.attachSearchFilter('#collection_chooser_collection_id');

    ajaxifyLinks(modal.body);
    ajaxifyImageUploadForm(modal);

    $('a.suggested-tag').on('click', function () {
      $('#id_q').val('');
      searchController.search({
        tag: $(this).text(),
        collection_id: $('#collection_chooser_collection_id').val(),
      });
      return false;
    });

    // Reinitialize tabs to hook up tab event listeners in the modal
    initTabs();
  },
  image_chosen: function (modal, jsonData) {
    modal.respond('imageChosen', jsonData.result);
    modal.close();
  },
  duplicate_found: function (modal, jsonData) {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    $('.use-new-image', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });
    $('.use-existing-image', modal.body).on('click', function () {
      var form = $(this).closest('form');
      var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();
      modal.postForm(this.href, { csrfmiddlewaretoken: CSRFToken });
      return false;
    });
  },
  reshow_upload_form: function (modal, jsonData) {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    initTabs();
    ajaxifyImageUploadForm(modal);
  },
  select_format: function (modal) {
    var decorativeImage = document.querySelector(
      '#id_image-chooser-insertion-image_is_decorative',
    );
    var altText = document.querySelector(
      '#id_image-chooser-insertion-alt_text',
    );
    var altTextLabel = document.querySelector(
      '[for="id_image-chooser-insertion-alt_text"]',
    );

    if (decorativeImage.checked) {
      disableAltText();
    } else {
      enableAltText();
    }

    decorativeImage.addEventListener('change', function (event) {
      if (event.target.checked) {
        disableAltText();
      } else {
        enableAltText();
      }
    });

    function disableAltText() {
      altText.setAttribute('disabled', 'disabled');
      altTextLabel.classList.remove('required');
    }

    function enableAltText() {
      altText.removeAttribute('disabled');
      altTextLabel.classList.add('required');
    }

    $('form', modal.body).on('submit', function () {
      $.post(this.action, $(this).serialize(), modal.loadResponseText, 'text');

      return false;
    });
  },
};
