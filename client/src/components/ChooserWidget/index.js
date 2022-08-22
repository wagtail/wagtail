import { chooserModalOnloadHandlers } from '../../includes/chooserModal';

export class Chooser {
  modalOnloadHandlers = chooserModalOnloadHandlers;

  titleStateKey = 'title'; // key used in the 'state' dictionary to hold the human-readable title
  editUrlStateKey = 'edit_url'; // key used in the 'state' dictionary to hold the URL of the edit page
  chosenResponseName = 'chosen'; // identifier for the ModalWorkflow response that indicates an item was chosen

  constructor(id) {
    this.initHTMLElements(id);
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

  initHTMLElements(id) {
    this.chooserElement = document.getElementById(`${id}-chooser`);
    this.titleElement = this.chooserElement.querySelector(
      '[data-chooser-title]',
    );
    this.input = document.getElementById(id);
    this.editLink = this.chooserElement.querySelector('.edit-link');
    this.chooserBaseUrl = this.chooserElement.dataset.chooserUrl;
  }

  getStateFromHTML() {
    /*
        Construct initial state of the chooser from the rendered (static) HTML.
        State is either null (= no item chosen) or a dict of id, title and edit_url.

        The result returned from the chooser modal (see get_chosen_response_data in
        wagtail.admin.views.generic.chooser.ChosenView) is a superset of this, and can therefore be
        passed directly to chooser.setState.
        */
    if (this.input.value) {
      const state = {
        id: this.input.value,
      };
      if (this.titleElement && this.titleStateKey) {
        state[this.titleStateKey] = this.titleElement.textContent;
      }
      if (this.editLink && this.editUrlStateKey) {
        state[this.editUrlStateKey] = this.editLink.getAttribute('href');
      }
      return state;
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
    if (this.titleElement && this.titleStateKey) {
      this.titleElement.textContent = newState[this.titleStateKey];
    }
    this.chooserElement.classList.remove('blank');
    if (this.editLink) {
      const editUrl = newState[this.editUrlStateKey];
      if (editUrl) {
        this.editLink.setAttribute('href', editUrl);
        this.editLink.classList.remove('w-hidden');
      } else {
        this.editLink.classList.add('w-hidden');
      }
    }
  }

  getTextLabel(opts) {
    if (!this.state) return null;
    const result = this.state[this.titleStateKey];
    if (opts && opts.maxLength && result.length > opts.maxLength) {
      return result.substring(0, opts.maxLength - 1) + '…';
    }
    return result;
  }

  focus() {
    if (this.state) {
      this.chooserElement.querySelector('.chosen .action-choose').focus();
    } else {
      this.chooserElement.querySelector('.unchosen .action-choose').focus();
    }
  }

  getModalUrl() {
    return this.chooserBaseUrl;
  }

  getModalUrlParams() {
    return null;
  }

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.getModalUrl(),
      urlParams: this.getModalUrlParams(),
      onload: this.modalOnloadHandlers,
      responses: {
        [this.chosenResponseName]: (result) => {
          this.setState(result);
        },
      },
    });
  }
}

export class ChooserFactory {
  widgetClass = Chooser;

  constructor(html, idPattern) {
    this.html = html;
    this.idPattern = idPattern;
  }

  render(placeholder, name, id, initialState) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    // eslint-disable-next-line no-param-reassign
    placeholder.outerHTML = html;
    // eslint-disable-next-line new-cap
    const chooser = new this.widgetClass(id);
    chooser.setState(initialState);
    return chooser;
  }
}
