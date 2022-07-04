import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  validateCreationForm,
  initPrefillTitleFromFilename,
  SearchController,
} from '../../includes/chooserModal';

class ImageChooserModalOnloadHandlerFactory {
  constructor() {
    this.searchController = null;
  }

  ajaxifyLinks(modal, containerElement) {
    $('a.image-choice', containerElement).on('click', (event) => {
      modal.loadUrl(event.currentTarget.href);
      return false;
    });

    $('.pagination a', containerElement).on('click', (event) => {
      this.searchController.fetchResults(event.currentTarget.href);
      return false;
    });
  }

  initSearchController(modal) {
    this.searchController = new SearchController({
      form: $('form.image-search', modal.body),
      containerElement: modal.body,
      resultsContainerSelector: '#search-results',
      onLoadResults: (containerElement) => {
        this.ajaxifyLinks(modal, containerElement);
      },
    });
    this.searchController.attachSearchInput('#id_q');
    this.searchController.attachSearchFilter('#id_collection_id');
  }

  ajaxifyImageUploadForm(modal) {
    $('form[data-chooser-modal-creation-form]', modal.body).on(
      'submit',
      (event) => {
        if (validateCreationForm(event.currentTarget)) {
          submitCreationForm(modal, event.currentTarget, {
            errorContainerSelector: '#tab-upload',
          });
        }
        return false;
      },
    );

    initPrefillTitleFromFilename(modal, {
      fileFieldSelector: '#id_image-chooser-upload-file',
      titleFieldSelector: '#id_image-chooser-upload-title',
      eventName: 'wagtail:images-upload',
    });
  }

  onLoadChooseStep(modal) {
    this.initSearchController(modal);
    this.ajaxifyLinks(modal, modal.body);
    this.ajaxifyImageUploadForm(modal);

    $('a.suggested-tag').on('click', (event) => {
      $('#id_q').val('');
      this.searchController.search({
        tag: $(event.currentTarget).text(),
        collection_id: $('#id_collection_id').val(),
      });
      return false;
    });

    // Reinitialize tabs to hook up tab event listeners in the modal
    initTabs();
  }

  onLoadChosenStep(modal, jsonData) {
    modal.respond('chosen', jsonData.result);
    modal.close();
  }

  onLoadDuplicateFoundStep(modal, jsonData) {
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
  }

  onLoadReshowCreationFormStep(modal, jsonData) {
    $('#tab-upload', modal.body).replaceWith(jsonData.htmlFragment);
    initTabs();
    this.ajaxifyImageUploadForm(modal);
  }

  onLoadSelectFormatStep(modal) {
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
  }

  getOnLoadHandlers() {
    return {
      choose: (modal, jsonData) => {
        this.onLoadChooseStep(modal, jsonData);
      },
      chosen: (modal, jsonData) => {
        this.onLoadChosenStep(modal, jsonData);
      },
      duplicate_found: (modal, jsonData) => {
        this.onLoadDuplicateFoundStep(modal, jsonData);
      },
      reshow_creation_form: (modal, jsonData) => {
        this.onLoadReshowCreationFormStep(modal, jsonData);
      },
      select_format: (modal, jsonData) => {
        this.onLoadSelectFormatStep(modal, jsonData);
      },
    };
  }
}

window.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new ImageChooserModalOnloadHandlerFactory().getOnLoadHandlers();
