import { Chooser, ChooserFactory } from '../../components/ChooserWidget';

class PageChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = PageChooserModal;

  titleStateKey = 'adminTitle';
  editUrlStateKey = 'editUrl';

  constructor(id, arg1, arg2) {
    let opts;
    if (arg2 || typeof arg1 === 'number') {
      /* old-style args: (id, parentId, opts) */
      opts = { parent_id: arg1, ...arg2 };
    } else {
      /* new style args: (id, opts) where opts includes 'parent_id' */
      opts = arg1 || {};
    }
    super(id, opts);
  }

  getStateFromHTML() {
    const state = super.getStateFromHTML();
    if (state) {
      state.parentId = this.opts.parent_id;
    }
    return state;
  }

  getModalOptions() {
    const opts = {
      model_names: this.opts.model_names,
      target_pages: this.opts.target_pages,
      match_subclass: this.opts.match_subclass,
      can_choose_root: this.opts.can_choose_root,
      user_perms: this.opts.user_perms,
    };
    if (this.state && this.state.parentId) {
      opts.parentId = this.state.parentId;
    }
    return opts;
  }
}
window.PageChooser = PageChooser;

class PageChooserFactory extends ChooserFactory {
  widgetClass = PageChooser;
}
window.PageChooserFactory = PageChooserFactory;

function createPageChooser(id, parentId, options) {
  /* RemovedInWagtail50Warning */
  return new PageChooser(id, parentId, options);
}
window.createPageChooser = createPageChooser;
