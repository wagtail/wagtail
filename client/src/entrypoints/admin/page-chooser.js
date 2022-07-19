class PageChooser {
  constructor(id, parentId, options) {
    this.chooserElement = document.getElementById(`${id}-chooser`);
    this.pageTitle = this.chooserElement.querySelector('.title');
    this.input = document.getElementById(id);
    this.editLink = this.chooserElement.querySelector('.edit-link');
    this.chooserBaseUrl = this.chooserElement.dataset.chooserUrl;
    this.initialParentId = parentId;
    this.options = options;

    this.state = this.getStateFromHTML();

    /* hook up chooser API to the buttons */
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
    Construct initial state of the chooser from the rendered (static) HTML and arguments passed to
    createPageChooser. State is either null (= no page chosen) or a dict of id, parentId,
    adminTitle (the admin display title) and editUrl.
    The result returned from the page chooser modal (which is ultimately built from the data
    attributes in wagtailadmin/chooser/tables/page_title_cell.html) is a superset of this, and can
    therefore be passed directly to chooser.setState.
    */
    if (this.input.value) {
      return {
        id: this.input.value,
        parentId: this.initialParentId,
        adminTitle: this.pageTitle.innerText,
        editUrl: this.editLink.getAttribute('href'),
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
    this.pageTitle.innerText = newState.adminTitle;
    this.chooserElement.classList.remove('blank');
    this.editLink.setAttribute('href', newState.editUrl);
  }

  getTextLabel(opts) {
    if (!this.state) return null;
    const result = this.state.adminTitle;
    if (opts && opts.maxLength && result.length > opts.maxLength) {
      return result.substring(0, opts.maxLength - 1) + '…';
    }
    return result;
  }

  focus() {
    this.chooserElement.querySelector('.action-choose').focus();
  }

  getModalUrl() {
    let url = this.chooserBaseUrl;
    if (this.state && this.state.parentId) {
      url += this.state.parentId + '/';
    }
    return url;
  }

  getModalUrlParams() {
    const urlParams = { page_type: this.options.model_names.join(',') };
    if (this.options.target_pages) {
      urlParams.target_pages = this.options.target_pages;
    }
    if (this.options.match_subclass) {
      urlParams.match_subclass = this.options.match_subclass;
    }
    if (this.options.can_choose_root) {
      urlParams.can_choose_root = 'true';
    }
    if (this.options.user_perms) {
      urlParams.user_perms = this.options.user_perms;
    }
    return urlParams;
  }

  openChooserModal() {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.getModalUrl(),
      urlParams: this.getModalUrlParams(),
      // eslint-disable-next-line no-undef
      onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        pageChosen: (result) => {
          this.setState(result);
        },
      },
    });
  }
}

function createPageChooser(id, parentId, options) {
  return new PageChooser(id, parentId, options);
}
window.createPageChooser = createPageChooser;
