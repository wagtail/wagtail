export class Panel {
  constructor(opts) {
    this.type = opts.type;
    this.prefix = opts.prefix;
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
  #boundWidget; // Cached bound widget instance, populated by getBoundWidget()

  constructor(opts) {
    super(opts);
    this.fieldName = opts.fieldName;
    this.widget = opts.widget;
  }

  getBoundWidget() {
    if (this.#boundWidget !== undefined) return this.#boundWidget;

    // Widget classes created before Wagtail 7.1 may not have a `getByName` method :-(
    if (this.widget.getByName) {
      this.#boundWidget = this.widget.getByName(this.fieldName, document.body);
    } else {
      this.#boundWidget = null;
    }
    return this.#boundWidget;
  }

  getPanelByName(name) {
    if (name === this.fieldName) return this;
    return null;
  }

  getErrorMessage() {
    const errorContainer = document.getElementById(`${this.prefix}-errors`);
    return errorContainer?.querySelector('.error-message')?.textContent?.trim();
  }

  setErrorMessage(message) {
    const errorContainerId = `${this.prefix}-errors`;
    const errorContainer = document.getElementById(errorContainerId);
    if (!errorContainer) return;

    const input = this.getBoundWidget()?.input;

    if (!message) {
      errorContainer.innerHTML = '';
      if (input) {
        input.removeAttribute('aria-invalid');

        const describedBy = input.getAttribute('aria-describedby') || '';
        const newDescribedBy = describedBy
          .split(' ')
          .filter((id) => id !== errorContainerId)
          .join(' ');
        input.setAttribute('aria-describedby', newDescribedBy);
      }
    } else {
      errorContainer.innerHTML = `
        <svg class="icon icon-warning w-field__errors-icon" aria-hidden="true"><use href="#icon-warning"></use></svg>
        <p class="error-message"></p>
      `;
      errorContainer.querySelector('.error-message').textContent = message;
      if (input) {
        input.setAttribute('aria-invalid', 'true');

        const describedBy = input.getAttribute('aria-describedby') || '';
        const describedByIds = describedBy.split(' ').filter(Boolean);
        if (!describedByIds.includes(errorContainerId)) {
          describedByIds.push(errorContainerId);
        }
        input.setAttribute('aria-describedby', describedByIds.join(' '));
      }
    }
  }
}
