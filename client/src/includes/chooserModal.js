/* global ModalWorkflow */

import $ from 'jquery';
import { initTabs } from './tabs';
import { gettext } from '../utils/gettext';

const validateCreationForm = (form) => {
  let hasErrors = false;
  form.querySelectorAll('input[required]').forEach((input) => {
    if (!input.value) {
      hasErrors = true;
      if (!input.hasAttribute('aria-invalid')) {
        input.setAttribute('aria-invalid', 'true');
        const field = input.closest('[data-field]');
        field.classList.add('w-field--error');
        const errors = field.querySelector('[data-field-errors]');
        const icon = errors.querySelector('.icon');
        if (icon) {
          icon.removeAttribute('hidden');
        }
        const errorElement = document.createElement('p');
        errorElement.classList.add('error-message');
        errorElement.textContent = gettext('This field is required.');
        errors.appendChild(errorElement);
      }
    }
  });
  if (hasErrors) {
    setTimeout(() => {
      // clear any loading state on progress buttons
      const attr = 'data-w-progress-loading-value';
      form.querySelectorAll(`[${attr}~="true"]`).forEach((element) => {
        element.removeAttribute(attr);
      });
    }, 500);
  }
  return !hasErrors;
};

const submitCreationForm = (modal, form, { errorContainerSelector }) => {
  const formdata = new FormData(form);

  $.ajax({
    url: form.action,
    data: formdata,
    processData: false,
    contentType: false,
    type: 'POST',
    dataType: 'text',
    success: modal.loadResponseText,
    error(response, textStatus, errorThrown) {
      const message =
        gettext(
          'Report this error to your website administrator with the following information:',
        ) +
        '<br />' +
        errorThrown +
        ' - ' +
        response.status;
      $(errorContainerSelector, modal.body).append(
        '<div class="help-block help-critical">' +
          '<strong>' +
          gettext('Server Error') +
          ': </strong>' +
          message +
          '</div>',
      );
    },
  });
};

class SearchController {
  constructor(opts) {
    this.form = opts.form;
    this.containerElement = opts.containerElement;
    this.onLoadResults = opts.onLoadResults;
    this.resultsContainer = $(
      opts.resultsContainerSelector,
      this.containerElement,
    );
    this.inputDelay = opts.inputDelay || 200;

    this.searchUrl = this.form.attr('action');
    this.request = null;

    this.form.on('submit', () => {
      this.searchFromForm();
      return false;
    });
  }

  attachSearchInput(selector) {
    let timer;

    $(selector, this.containerElement).on('input', () => {
      if (this.request) {
        this.request.abort();
      }
      clearTimeout(timer);
      timer = setTimeout(() => {
        this.searchFromForm();
      }, this.inputDelay);
    });
  }

  attachSearchFilter(selector) {
    $(selector, this.containerElement).on('change', () => {
      this.searchFromForm();
    });
  }

  fetchResults(url, queryParams) {
    const requestOptions = {
      url: url,
      success: (resultsData) => {
        this.request = null;
        this.resultsContainer.html(resultsData);
        if (this.onLoadResults) {
          this.onLoadResults(this.resultsContainer);
        }
      },
      error() {
        this.request = null;
      },
    };
    if (queryParams) {
      requestOptions.data = queryParams;
    }
    this.request = $.ajax(requestOptions);
  }

  search(queryParams) {
    this.fetchResults(this.searchUrl, queryParams);
  }

  searchFromForm() {
    this.search(this.form.serialize());
  }
}

class ChooserModalOnloadHandlerFactory {
  constructor(opts) {
    this.chooseStepName = opts?.chooseStepName || 'choose';
    this.chosenStepName = opts?.chosenStepName || 'chosen';
    this.reshowCreationFormStepName =
      opts?.reshowCreationFormStepName || 'reshow_creation_form';
    this.chosenLinkSelector =
      opts?.chosenLinkSelector || 'a[data-chooser-modal-choice]';
    this.paginationLinkSelector =
      opts?.paginationLinkSelector || '.pagination a';
    this.searchFormSelector =
      opts?.searchFormSelector || 'form[data-chooser-modal-search]';
    this.resultsContainerSelector =
      opts?.resultsContainerSelector || '#search-results';
    this.searchInputSelectors = opts?.searchInputSelectors || ['#id_q'];
    this.searchFilterSelectors = opts?.searchFilterSelectors || [
      '[data-chooser-modal-search-filter]',
    ];
    this.chosenResponseName = opts?.chosenResponseName || 'chosen';
    this.searchInputDelay = opts?.searchInputDelay || 200;
    this.creationFormSelector =
      opts?.creationFormSelector || 'form[data-chooser-modal-creation-form]';
    this.creationFormTabSelector =
      opts?.creationFormTabSelector || '#tab-create';
    this.creationFormFileFieldSelector = opts?.creationFormFileFieldSelector;
    this.creationFormTitleFieldSelector = opts?.creationFormTitleFieldSelector;
    this.creationFormEventName = opts?.creationFormEventName;

    this.searchController = null;
  }

  ajaxifyLinks(modal, containerElement) {
    if (!this.searchController) {
      throw new Error(
        'Cannot call ajaxifyLinks until a SearchController is set up',
      );
    }

    $(this.chosenLinkSelector, containerElement).on('click', (event) => {
      modal.loadUrl(event.currentTarget.href);
      return false;
    });

    $(this.paginationLinkSelector, containerElement).on('click', (event) => {
      this.searchController.fetchResults(event.currentTarget.href);
      return false;
    });

    // Reinitialize tabs to hook up tab event listeners in the modal
    if (this.modalHasTabs(modal)) initTabs();

    this.updateMultipleChoiceSubmitEnabledState(modal);
    $('[data-multiple-choice-select]', containerElement).on('change', () => {
      this.updateMultipleChoiceSubmitEnabledState(modal);
    });
  }

  updateMultipleChoiceSubmitEnabledState(modal) {
    // update the enabled state of the multiple choice submit button depending on whether
    // any items have been selected
    if ($('[data-multiple-choice-select]:checked', modal.body).length) {
      $('[data-multiple-choice-submit]', modal.body).removeAttr('disabled');
    } else {
      $('[data-multiple-choice-submit]', modal.body).attr('disabled', true);
    }
  }

  modalHasTabs(modal) {
    return $('[data-tabs]', modal.body).length;
  }

    ajaxifyCreationForm(modal) {
    /* Convert the creation form to an AJAX submission */
    $(this.creationFormSelector, modal.body).on('submit', (event) => {
      if (validateCreationForm(event.currentTarget)) {
        submitCreationForm(modal, event.currentTarget, {
          errorContainerSelector: this.creationFormTabSelector,
        });
      }
      return false;
    });

    if (
      this.creationFormFileFieldSelector &&
      this.creationFormTitleFieldSelector
    ) {
      const fileField = $(this.creationFormFileFieldSelector, modal.body);
      const titleField = $(this.creationFormTitleFieldSelector, modal.body);

      fileField.attr({
        'data-controller': 'w-sync',
        'data-action': 'change->w-sync#apply',
        'data-w-sync-target-value': this.creationFormTitleFieldSelector,
        'data-w-sync-normalize-value': 'true',
        'data-w-sync-name-value': this.creationFormEventName,
      });

      titleField.attr({
        'data-controller': 'w-clean',
        'data-action': 'blur->w-clean#slugify',
      });
    }
  }


  initSearchController(modal) {
    this.searchController = new SearchController({
      form: $(this.searchFormSelector, modal.body),
      containerElement: modal.body,
      resultsContainerSelector: this.resultsContainerSelector,
      onLoadResults: (containerElement) => {
        this.ajaxifyLinks(modal, containerElement);
      },
      inputDelay: this.searchInputDelay,
    });
    this.searchInputSelectors.forEach((selector) => {
      this.searchController.attachSearchInput(selector);
    });
    this.searchFilterSelectors.forEach((selector) => {
      this.searchController.attachSearchFilter(selector);
    });
  }

  onLoadChooseStep(modal) {
    this.initSearchController(modal);
    this.ajaxifyLinks(modal, modal.body);
    this.ajaxifyCreationForm(modal);
    // Set up submissions of the "choose multiple items" form to open in the modal.
    modal.ajaxifyForm($('form[data-multiple-choice-form]', modal.body));
  }

  onLoadChosenStep(modal, jsonData) {
    modal.respond(this.chosenResponseName, jsonData.result);
    modal.close();
  }

  onLoadReshowCreationFormStep(modal, jsonData) {
    $(this.creationFormTabSelector, modal.body).replaceWith(
      jsonData.htmlFragment,
    );
    if (this.modalHasTabs(modal)) initTabs();
    this.ajaxifyCreationForm(modal);
  }

  getOnLoadHandlers() {
    return {
      [this.chooseStepName]: (modal, jsonData) => {
        this.onLoadChooseStep(modal, jsonData);
      },
      [this.chosenStepName]: (modal, jsonData) => {
        this.onLoadChosenStep(modal, jsonData);
      },
      [this.reshowCreationFormStepName]: (modal, jsonData) => {
        this.onLoadReshowCreationFormStep(modal, jsonData);
      },
    };
  }
}

const chooserModalOnloadHandlers =
  new ChooserModalOnloadHandlerFactory().getOnLoadHandlers();

class ChooserModal {
  onloadHandlers = chooserModalOnloadHandlers;
  chosenResponseName = 'chosen'; // identifier for the ModalWorkflow response that indicates an item was chosen

  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getURL(opts) {
    return this.baseUrl;
  }

  getURLParams(opts) {
    const urlParams = {};
    if (opts.multiple) {
      urlParams.multiple = 1;
    }
    if (opts.linkedFieldFilters) {
      Object.assign(urlParams, opts.linkedFieldFilters);
    }
    return urlParams;
  }

  open(opts, callback) {
    ModalWorkflow({
      url: this.getURL(opts || {}),
      urlParams: this.getURLParams(opts || {}),
      onload: this.onloadHandlers,
      responses: {
        [this.chosenResponseName]: (result) => {
          callback(result);
        },
      },
    });
  }
}

export {
  validateCreationForm,
  submitCreationForm,
  SearchController,
  ChooserModalOnloadHandlerFactory,
  chooserModalOnloadHandlers,
  ChooserModal,
};
