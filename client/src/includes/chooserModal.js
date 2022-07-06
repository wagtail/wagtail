/* eslint-disable max-classes-per-file */
import $ from 'jquery';
import { initTabs } from './tabs';
import { initTooltips } from './initTooltips';
import { gettext } from '../utils/gettext';

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

      // allow an event handler to customise data or call event.preventDefault to stop any title pre-filling
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

    // Reinitialise any tooltips
    initTooltips();
  }

  // eslint-disable-next-line class-methods-use-this
  modalHasTabs(modal) {
    return $('[data-tabs]', modal.body).length;
  }

  ajaxifyCreationForm(modal) {
    /* Convert the creation form to an AJAX submission */
    $(this.creationFormSelector, modal.body).on('submit', (event) => {
      submitCreationForm(modal, event.currentTarget, {
        errorContainerSelector: this.creationFormTabSelector,
      });

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

export {
  submitCreationForm,
  initPrefillTitleFromFilename,
  SearchController,
  ChooserModalOnloadHandlerFactory,
  chooserModalOnloadHandlers,
};
