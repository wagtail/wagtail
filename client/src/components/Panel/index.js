export class Panel {
  constructor(type) {
    this.type = type;
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
  constructor(type, children) {
    super(type);
    this.children = children;
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
  constructor(type, fieldName, widget) {
    super(type);
    this.fieldName = fieldName;
    this.widget = widget;
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
