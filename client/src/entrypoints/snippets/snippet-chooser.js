/* global wagtailConfig */

class SnippetChooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS;

  constructor(id) {
    this.chooserElement = document.getElementById(`${id}-chooser`);
    this.titleElement = this.chooserElement.querySelector('.title');
    this.input = document.getElementById(id);
    this.editLink = this.chooserElement.querySelector('.edit-link');
    this.chooserBaseUrl = this.chooserElement.dataset.chooserUrl;

    this.state = this.getStateFromHtml();

    for (const btn of this.chooserElement.querySelectorAll('.action-choose')) {
      btn.addEventListener('click', () => {
        this.openChooserModal();
      });
    }
    for (const btn of this.chooserElement.querySelectorAll('.action-clear')) {
      btn.addEventListener('click', () => {
        this.clear();
      });
    }
  }

  getStateFromHtml() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no snippet chosen) or a dict of id, string and
    edit_link.

    The result returned from the snippet chooser modal (see wagtail.snippets.views.chooser.chosen)
    is a superset of this, and can therefore be passed directly to chooser.setState.
    */

    if (this.input.value) {
      return {
        id: this.input.value,
        edit_link: this.editLink.getAttribute('href'),
        string: this.titleElement.innerText,
      };
    } else {
      return null;
    }
  }

  getState() {
    return this.state;
  }
  getValue() {
    return this.state && this.state.id;
  }
  setState(newState) {
    this.state = newState;
    if (newState) {
      this.renderState(newState);
    } else {
      this.renderEmptyState();
    }
  }
  clear() {
    this.setState(null);
  }
  renderEmptyState() {
    this.input.setAttribute('value', '');
    this.chooserElement.classList.add('blank');
  }
  renderState(newState) {
    this.input.setAttribute('value', newState.id);
    this.titleElement.innerText = newState.string;
    this.chooserElement.classList.remove('blank');
    this.editLink.setAttribute('href', newState.edit_link);
  }
  getTextLabel(opts) {
    if (!this.state) return null;
    const result = this.state.string;
    if (opts && opts.maxLength && result.length > opts.maxLength) {
      return result.substring(0, opts.maxLength - 1) + '…';
    }
    return result;
  }
  focus() {
    this.chooserElement.querySelector('.action-choose').focus();
  }

  openChooserModal() {
    let urlQuery = '';
    if (wagtailConfig.ACTIVE_CONTENT_LOCALE) {
      // The user is editing a piece of translated content.
      // Pass the locale along as a request parameter. If this
      // snippet is also translatable, the results will be
      // pre-filtered by this locale.
      urlQuery = '?locale=' + wagtailConfig.ACTIVE_CONTENT_LOCALE;
    }

    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.chooserBaseUrl + urlQuery,
      onload: this.modalOnloadHandlers,
      responses: {
        snippetChosen: (result) => {
          this.setState(result);
        },
      },
    });
  }
}

function createSnippetChooser(id) {
  return new SnippetChooser(id);
}
window.createSnippetChooser = createSnippetChooser;
