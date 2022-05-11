import $ from 'jquery';
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

      titleWidget.val(data.title);
    }
  });
};

class SearchController {
  constructor(opts) {
    this.form = opts.form;
    this.onLoadResults = opts.onLoadResults;
    this.resultsContainer = $(opts.resultsContainerSelector);
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

    $(selector).on('input', () => {
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
    $(selector).on('change', () => {
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

export { submitCreationForm, initPrefillTitleFromFilename, SearchController };
