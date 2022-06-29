import $ from 'jquery';

class DocumentChooser {
  constructor(id) {
    this.chooserElement = $('#' + id + '-chooser');
    this.docTitle = this.chooserElement.find('.title');
    this.input = $('#' + id);
    this.editLink = this.chooserElement.find('.edit-link');
    this.chooserBaseUrl = this.chooserElement.data('chooserUrl');

    this.state = this.getStateFromHTML();

    $('.action-choose', this.chooserElement).on('click', () => {
      this.openChooserModal();
    });

    $('.action-clear', this.chooserElement).on('click', () => {
      this.clear();
    });
  }

  getStateFromHTML() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML.
    State is either null (= no document chosen) or a dict of id, title and edit_link.

    The result returned from the document chooser modal (see get_document_chosen_response in
    wagtail.documents.views.chooser) is a superset of this, and can therefore be passed directly to
    chooser.setState.
    */
    if (this.input.val()) {
      return {
        id: this.input.val(),
        edit_link: this.editLink.attr('href'),
        title: this.docTitle.text(),
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
    this.input.val('');
    this.chooserElement.addClass('blank');
  }

  renderState(newState) {
    this.input.val(newState.id);
    this.docTitle.text(newState.title);
    this.chooserElement.removeClass('blank');
    this.editLink.attr('href', newState.edit_link);
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
    $('.action-choose', this.chooserElement).focus();
  }

  getModalUrl() {
    return this.chooserBaseUrl;
  }

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.chooserBaseUrl,
      // eslint-disable-next-line no-undef
      onload: DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
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
