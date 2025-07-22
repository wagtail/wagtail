export class Panel {
  /**
   * Type of the panel; will generally match the Python-side panel class name
   * (e.g., `FieldPanel`, `PanelGroup`) */
  type: string;
  /** Prefix for the panel's HTML elements (e.g., `field-`) */
  prefix: string;

  constructor(opts: { type: string; prefix: string }) {
    this.type = opts.type;
    this.prefix = opts.prefix;
  }

  /**
   * Return any descendant panel (including self) that matches the given field or relation name,
   * or `null` if there is no match
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getPanelByName(_name: string): Panel | null {
    // The base panel definition has no notion of descendants or a name of its own, so just return null
    return null;
  }
}

export class PanelGroup extends Panel {
  /** Array of child panels */
  children: Panel[];

  constructor(opts: { type: string; prefix: string; children: Panel[] }) {
    super(opts);
    this.children = opts.children;
  }

  getPanelByName(name: string): Panel | null {
    for (const child of this.children) {
      const panel = child.getPanelByName(name);
      if (panel) return panel;
    }
    return null;
  }
}

export class FieldPanel extends Panel {
  /** Cached bound widget instance, populated by `getBoundWidget()` */
  #boundWidget: any;
  /** Name of the field this panel is associated with */
  fieldName: string;
  /** Widget class used for rendering the field */
  widget: any;

  constructor(opts: {
    type: string;
    prefix: string;
    fieldName: string;
    widget: any;
  }) {
    super(opts);
    this.fieldName = opts.fieldName;
    this.widget = opts.widget;
  }

  getBoundWidget() {
    if (this.#boundWidget !== undefined) return this.#boundWidget;

    // Widget classes created before Wagtail 7.1 may not have a `getByName` method :-(
    if (this.widget.getByName) {
      const wrapper = document.getElementById(`${this.prefix}-wrapper`);
      this.#boundWidget = this.widget.getByName(
        this.fieldName,
        wrapper || document.body,
      );
    } else {
      this.#boundWidget = null;
    }
    return this.#boundWidget;
  }

  getPanelByName(name: string): Panel | null {
    if (name === this.fieldName) return this;
    return null;
  }

  getErrorMessage() {
    const errorContainer = document.getElementById(`${this.prefix}-errors`);
    return errorContainer?.querySelector('.error-message')?.textContent?.trim();
  }

  setErrorMessage(message: string | null) {
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
          .filter((id: string) => id !== errorContainerId)
          .join(' ');
        input.setAttribute('aria-describedby', newDescribedBy);
      }
    } else {
      errorContainer.innerHTML = `
        <svg class="icon icon-warning w-field__errors-icon" aria-hidden="true"><use href="#icon-warning"></use></svg>
        <p class="error-message"></p>
      `;
      (
        errorContainer.querySelector('.error-message') as HTMLElement
      ).textContent = message;
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
