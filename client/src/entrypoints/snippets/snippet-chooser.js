import $ from 'jquery';

/* global wagtailConfig */

class SnippetChooser {
  constructor(id) {
    this.chooserElement = $('#' + id + '-chooser');
    this.docTitle = this.chooserElement.find('.title');
    this.input = $('#' + id);
    this.editLink = this.chooserElement.find('.edit-link');
    this.chooserBaseUrl = this.chooserElement.data('chooserUrl');

    this.state = this.getStateFromHtml();

    $('.action-choose', this.chooserElement).on('click', () => {
      this.openChooserModal();
    });

    $('.action-clear', this.chooserElement).on('click', () => {
      this.clear();
    });
  }

  getStateFromHtml() {
    /*
    Construct initial state of the chooser from the rendered (static) HTML
    and arguments passed to createSnippetChooser.
    State is either null (= no document chosen) or a dict of id, string and
    edit_link.

    The result returned from the snippet chooser modal (see wagtail.snippets.views.chooser.chosen)
    is a superset of this, and can therefore be passed directly to chooser.setState.
    */

    if (this.input.val()) {
      return {
        id: this.input.val(),
        edit_link: this.editLink.attr('href'),
        string: this.docTitle.text(),
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
    this.docTitle.text(newState.string);
    this.chooserElement.removeClass('blank');
    this.editLink.attr('href', newState.edit_link);
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
    $('.action-choose', this.chooserElement).focus();
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
      // eslint-disable-next-line no-undef
      onload: SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS,
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
