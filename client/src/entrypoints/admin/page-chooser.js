import { Chooser } from '../../components/ChooserWidget';

class PageChooser extends Chooser {
  // eslint-disable-next-line no-undef
  modalOnloadHandlers = PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;
  titleStateKey = 'adminTitle';
  editUrlStateKey = 'editUrl';
  chosenResponseName = 'pageChosen';

  constructor(id, parentId, options) {
    this.initialParentId = parentId;
    this.options = options;
    super(id);
  }

  getStateFromHTML() {
    const state = super.getStateFromHTML();
    if (state) {
      state.parentId = this.initialParentId;
    }
    return state;
  }

  getModalUrl() {
    let url = super.getModalUrl();
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
}
window.PageChooser = PageChooser;

function createPageChooser(id, parentId, options) {
  /* RemovedInWagtail50Warning */
  return new PageChooser(id, parentId, options);
}
window.createPageChooser = createPageChooser;
