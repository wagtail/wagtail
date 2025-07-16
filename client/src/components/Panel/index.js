export class Panel {
  constructor(opts) {
    this.type = opts.type;
  }

  getPanelByName(/* name */) {
    /* Return any descendant panel (including self) that matches the given field or relation name,
     * or null if there is no match
     */

    // The base panel definition has no notion of descendants or a name of its own, so just return null
    return null;
  }
}

export class PanelGroup extends Panel {
  constructor(opts) {
    super(opts);
    this.children = opts.children;
  }

  getPanelByName(name) {
    for (const child of this.children) {
      const panel = child.getPanelByName(name);
      if (panel) return panel;
    }
    return null;
  }
}

export class FieldPanel extends Panel {
  constructor(opts) {
    super(opts);
    this.fieldName = opts.fieldName;
    this.widget = opts.widget;
  }

  getBoundWidget() {
    // Widget classes created before Wagtail 7.1 may not have a `getByName` method :-(
    if (this.widget.getByName) {
      return this.widget.getByName(this.fieldName, document.body);
    }
    return null;
  }

  getPanelByName(name) {
    if (name === this.fieldName) return this;
    return null;
  }
}
