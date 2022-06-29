class DocumentChooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS;

  constructor(id) {
    this.chooserElement = document.getElementById(`${id}-chooser`);
    this.titleElement = this.chooserElement.querySelector('.title');
    this.input = document.getElementById(id);
    this.editLink = this.chooserElement.querySelector('.edit-link');
    this.chooserBaseUrl = this.chooserElement.dataset.chooserUrl;

    this.state = this.getStateFromHTML();

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

  getStateFromHTML() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no document chosen) or a dict of id, title and edit_link.

    The result returned from the document chooser modal (see get_document_chosen_response in
    wagtail.documents.views.chooser) is a superset of this, and can therefore be passed directly to
    chooser.setState.
    */
    if (this.input.value) {
      return {
        id: this.input.value,
        edit_link: this.editLink.getAttribute('href'),
        title: this.titleElement.innerText,
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
    this.titleElement.innerText = newState.title;
    this.chooserElement.classList.remove('blank');
    this.editLink.setAttribute('href', newState.edit_link);
  }

  getTextLabel(opts) {
    if (!this.state) return null;
    const result = this.state.title;
    if (opts && opts.maxLength && result.length > opts.maxLength) {
      return result.substring(0, opts.maxLength - 1) + '…';
    }
    return result;
  }

  focus() {
    this.chooserElement.querySelector('.action-choose').focus();
  }

  getModalUrl() {
    return this.chooserBaseUrl;
  }

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.chooserBaseUrl,
      onload: this.modalOnloadHandlers,
      responses: {
        documentChosen: (result) => {
          this.setState(result);
        },
      },
    });
  }
}

function createDocumentChooser(id) {
  return new DocumentChooser(id);
}
window.createDocumentChooser = createDocumentChooser;
