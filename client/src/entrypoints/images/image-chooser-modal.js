import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  initPrefillTitleFromFilename,
  SearchController,
} from '../../includes/chooserModal';

function ajaxifyImageUploadForm(modal) {
  $('form.image-upload', modal.body).on('submit', (event) => {
    if (!$('#id_image-chooser-upload-title', modal.body).val()) {
      const li = $('#id_image-chooser-upload-title', modal.body).closest('li');
      if (!li.hasClass('error')) {
        li.addClass('error');
        $('#id_image-chooser-upload-title', modal.body)
          .closest('.field-content')
          .append(
            '<p class="error-message"><span>This field is required.</span></p>',
          );
      }
      // eslint-disable-next-line no-undef
      setTimeout(cancelSpinner, 500);
    } else {
      submitCreationForm(modal, event.currentTarget, {
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
  chooser: (modal) => {
    let searchController;

    function ajaxifyLinks(context) {
      $('.listing a', context).on('click', (event) => {
        modal.loadUrl(event.currentTarget.href);
        return false;
      });

      $('.pagination a', context).on('click', (event) => {
        searchController.fetchResults(event.currentTarget.href);
        return false;
      });
    }

    searchController = new SearchController({
      form: $('form.image-search', modal.body),
      containerElement: modal.body,
      resultsContainerSelector: '#image-results',
      onLoadResults: (context) => {
        ajaxifyLinks(context);
      },
    });
    searchController.attachSearchInput('#id_q');
    searchController.attachSearchFilter('#collection_chooser_collection_id');

    ajaxifyLinks(modal.body);
    ajaxifyImageUploadForm(modal);

    $('a.suggested-tag').on('click', (event) => {
      $('#id_q').val('');
      searchController.search({
        tag: $(event.currentTarget).text(),
        collection_id: $('#collection_chooser_collection_id').val(),
      });
      return false;
    });

    // Reinitialize tabs to hook up tab event listeners in the modal
    initTabs();
  },
  image_chosen: (modal, jsonData) => {
    modal.respond('imageChosen', jsonData.result);
    modal.close();
  },
  duplicate_found: (modal, jsonData) => {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    $('.use-new-image', modal.body).on('click', (event) => {
      modal.loadUrl(event.currentTarget.href);
      return false;
    });
    $('.use-existing-image', modal.body).on('click', (event) => {
      var form = $(event.currentTarget).closest('form');
      var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();
      modal.postForm(event.currentTarget.href, {
        csrfmiddlewaretoken: CSRFToken,
      });
      return false;
    });
  },
  reshow_upload_form: (modal, jsonData) => {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    initTabs();
    ajaxifyImageUploadForm(modal);
  },
  select_format: (modal) => {
    var decorativeImage = document.querySelector(
      '#id_image-chooser-insertion-image_is_decorative',
    );
    var altText = document.querySelector(
      '#id_image-chooser-insertion-alt_text',
    );
    var altTextLabel = document.querySelector(
      '[for="id_image-chooser-insertion-alt_text"]',
    );

    function disableAltText() {
      altText.setAttribute('disabled', 'disabled');
      altTextLabel.classList.remove('required');
    }

    function enableAltText() {
      altText.removeAttribute('disabled');
      altTextLabel.classList.add('required');
    }

    if (decorativeImage.checked) {
      disableAltText();
    } else {
      enableAltText();
    }

    decorativeImage.addEventListener('change', (event) => {
      if (event.target.checked) {
        disableAltText();
      } else {
        enableAltText();
      }
    });

    $('form', modal.body).on('submit', (event) => {
      $.post(
        event.currentTarget.action,
        $(event.currentTarget).serialize(),
        modal.loadResponseText,
        'text',
      );

      return false;
    });
  },
};
