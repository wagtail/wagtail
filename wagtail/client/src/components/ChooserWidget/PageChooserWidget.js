/* global PageChooserModal */

import { Chooser, ChooserFactory } from '.';

export class PageChooser extends Chooser {
  chooserModalClass = PageChooserModal;

  titleStateKey = 'adminTitle';
  editUrlStateKey = 'editUrl';

  constructor(id, arg1, arg2) {
    let opts;
    if (arg2 || typeof arg1 === 'number') {
      /* old-style args: (id, parentId, opts) */
      opts = { parentId: arg1, ...arg2 };
    } else {
      /* new style args: (id, opts) where opts includes 'parentId' */
      opts = arg1 || {};
    }
    super(id, opts);
  }

  getStateFromHTML() {
    const state = super.getStateFromHTML();
    if (state) {
      state.parentId = this.opts.parentId;
    }
    return state;
  }

  getModalOptions() {
    const opts = {
      modelNames: this.opts.modelNames,
      targetPages: this.opts.targetPages,
      matchSubclass: this.opts.matchSubclass,
      canChooseRoot: this.opts.canChooseRoot,
      userPerms: this.opts.userPerms,
    };
    if (this.state && this.state.parentId) {
      opts.parentId = this.state.parentId;
    }
    return opts;
  }
}

export class PageChooserFactory extends ChooserFactory {
  widgetClass = PageChooser;
  chooserModalClass = PageChooserModal;

  getModalOptions() {
    return {
      modelNames: this.opts.modelNames,
      targetPages: this.opts.targetPages,
      matchSubclass: this.opts.matchSubclass,
      canChooseRoot: this.opts.canChooseRoot,
      userPerms: this.opts.userPerms,
    };
  }
}
