import { Chooser } from '../../components/ChooserWidget';

class PageChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = PageChooserModal;

  titleStateKey = 'adminTitle';
  editUrlStateKey = 'editUrl';

  constructor(id, parentId, options = {}) {
    super(id);
    this.initialParentId = parentId;
    this.options = options;
  }

  getStateFromHTML() {
    const state = super.getStateFromHTML();
    if (state) {
      state.parentId = this.initialParentId;
    }
    return state;
  }

  getModalOptions() {
    const opts = {
      model_names: this.options.model_names,
      target_pages: this.options.target_pages,
      match_subclass: this.options.match_subclass,
      can_choose_root: this.options.can_choose_root,
      user_perms: this.options.user_perms,
    };
    if (this.state && this.state.parentId) {
      opts.parentId = this.state.parentId;
    }
    return opts;
  }
}
window.PageChooser = PageChooser;

function createPageChooser(id, parentId, options) {
  /* RemovedInWagtail50Warning */
  return new PageChooser(id, parentId, options);
}
window.createPageChooser = createPageChooser;
