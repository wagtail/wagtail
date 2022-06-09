import $ from 'jquery';

import { chooserModalOnloadHandlers } from '../../includes/chooserModal';

export class Chooser {
  modalOnloadHandlers = chooserModalOnloadHandlers;

  constructor(id) {
    this.chooserElement = $('#' + id + '-chooser');
    this.titleElement = this.chooserElement.find('.title');
    this.input = $('#' + id);
    this.editLink = this.chooserElement.find('.edit-link');
    this.chooserBaseUrl = this.chooserElement.data('chooserUrl');

    this.state = this.getStateFromHtml();

    this.chooserElement.find('.action-choose').on('click', () => {
      this.openChooserModal();
    });
    this.chooserElement.find('.action-clear').on('click', () => {
      this.clear();
    });
  }

  getStateFromHtml() {
    /*
        Construct initial state of the chooser from the rendered (static) HTML.
        State is either null (= no item chosen) or a dict of id, title and edit_link.

        The result returned from the chooser modal (see get_chosen_response_data in
        wagtail.admin.views.generic.chooser.ChosenView) is a superset of this, and can therefore be
        passed directly to chooser.setState.
        */
    if (this.input.val()) {
      return {
        id: this.input.val(),
        edit_link: this.editLink.attr('href'),
        title: this.titleElement.text(),
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
    this.titleElement.text(newState.title);
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

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.chooserBaseUrl,
      onload: this.modalOnloadHandlers,
      responses: {
        chosen: (result) => {
          this.setState(result);
        },
      },
    });
  }
}
