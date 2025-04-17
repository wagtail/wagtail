/* global ModalWorkflow */

import $ from 'jquery';
import { initTabs } from './tabs';
import { gettext } from '../utils/gettext';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

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

const initPrefillTitleFromFilename = (
  modal,
  { fileFieldSelector, titleFieldSelector, eventName },
) => {
  const fileWidget = $(fileFieldSelector, modal.body);
  fileWidget.on('change', () => {
    const titleWidget = $(titleFieldSelector, modal.body);
    const title = titleWidget.val();
    // do not override a title that already exists (from manual editing or previous upload)
    if (title === '') {
      // The file widget value example: `C:\fakepath\image.jpg`
      const parts = fileWidget.val().split('\\');
      const filename = parts[parts.length - 1];

      // allow event handler to override filename (used for title) & provide maxLength as int to event
      const maxTitleLength =
        parseInt(titleWidget.attr('maxLength') || '0', 10) || null;
      const data = { title: filename.replace(/\.[^.]+$/, '') };

      // allow an event handler to customize data or call event.preventDefault to stop any title pre-filling
      const form = fileWidget.closest('form').get(0);

      if (eventName) {
        const event = form.dispatchEvent(
          new CustomEvent(eventName, {
            bubbles: true,
            cancelable: true,
            detail: {
              data: data,
              filename: filename,
              maxTitleLength: maxTitleLength,
            },
          }),
        );

        if (!event) return; // do not set a title if event.preventDefault(); is called by handler
      }

      titleWidget.val(data.title);
    }
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

    /* If this form has a file and title field, set up the title to be prefilled from the title */
    if (
      this.creationFormFileFieldSelector &&
      this.creationFormTitleFieldSelector
    ) {
      initPrefillTitleFromFilename(modal, {
        fileFieldSelector: this.creationFormFileFieldSelector,
        titleFieldSelector: this.creationFormTitleFieldSelector,
        eventName: this.creationFormEventName,
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
    if (WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE) {
      // The user is editing a piece of translated content.
      // Pass the locale along as a request parameter. If this
      // model is also translatable, the results will be
      // pre-filtered by this locale.
      urlParams.locale = WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE;
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
  initPrefillTitleFromFilename,
  SearchController,
  ChooserModalOnloadHandlerFactory,
  chooserModalOnloadHandlers,
  ChooserModal,
};
