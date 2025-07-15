export class Panel {
  constructor(type) {
    this.type = type;
  }

  collectWidgets() {
    /* Insert any widgets that this panel manages into the `collection` dict. */
  }

  getWidgets() {
    /* Return a dict of widgets that this panel manages. */
    const collection = {};
    this.collectWidgets(collection);
    return collection;
  }
}

export class PanelGroup extends Panel {
  constructor(type, children) {
    super(type);
    this.children = children;
  }

  collectWidgets(collection) {
    /* Insert any widgets that this panel group manages into the `collection` dict. */
    this.children.forEach((child) => {
      child.collectWidgets(collection);
    });
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

  collectWidgets(collection) {
    let boundWidget;
    // Widget classes created before Wagtail 7.1 may not have a `getByName` method :-(
    try {
      boundWidget = this.getBoundWidget();
    } catch (error) {
      if (error.name === 'InputNotFoundError') {
        return; // Skip adding this widget if not found
      }
      throw error; // Re-throw other errors
    }
    if (boundWidget) {
      // eslint-disable-next-line no-param-reassign
      collection[this.fieldName] = boundWidget;
    }
  }
}
