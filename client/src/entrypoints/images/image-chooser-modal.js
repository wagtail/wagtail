import $ from 'jquery';
import {
  ChooserModalOnloadHandlerFactory,
  ChooserModal,
} from '../../includes/chooserModal';

class ImageChooserModalOnloadHandlerFactory extends ChooserModalOnloadHandlerFactory {
  ajaxifyLinks(modal, context) {
    super.ajaxifyLinks(modal, context);

    $('a.upload-one-now').on('click', (event) => {
      // Set current collection ID at upload form tab
      const collectionId = $('#id_collection_id').val();
      if (collectionId) {
        $('#id_image-chooser-upload-collection').val(collectionId);
      }

      event.preventDefault();
    });
  }

  onLoadChooseStep(modal) {
    super.onLoadChooseStep(modal);

    $('a.suggested-tag').on('click', (event) => {
      $('#id_q').val('');
      this.searchController.search({
        tag: $(event.currentTarget).text(),
        collection_id: $('#id_collection_id').val(),
      });
      return false;
    });
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
    const handlers = super.getOnLoadHandlers();
    handlers.duplicate_found = (modal, jsonData) => {
      this.onLoadDuplicateFoundStep(modal, jsonData);
    };
    handlers.select_format = (modal, jsonData) => {
      this.onLoadSelectFormatStep(modal, jsonData);
    };
    return handlers;
  }
}

window.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new ImageChooserModalOnloadHandlerFactory({
    creationFormFileFieldSelector: '#id_image-chooser-upload-file',
    creationFormTitleFieldSelector: '#id_image-chooser-upload-title',
    creationFormEventName: 'wagtail:images-upload',
    creationFormTabSelector: '#tab-upload',
  }).getOnLoadHandlers();

class ImageChooserModal extends ChooserModal {
  onloadHandlers = window.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;
}
window.ImageChooserModal = ImageChooserModal;
