import { setAttrs } from '../../utils/attrs';
import { gettext } from '../../utils/gettext';
import { runInlineScripts } from '../../utils/runInlineScripts';

/**
 * Given an element or a NodeList, return the first element that matches the selector.
 * This can be the top-level element itself or a descendant.
 */
export const querySelectorIncludingSelf = (elementOrNodeList, selector) => {
  // if elementOrNodeList not iterable, it must be a single element
  const nodeList = elementOrNodeList.forEach
    ? elementOrNodeList
    : [elementOrNodeList];

  for (let i = 0; i < nodeList.length; i += 1) {
    const container = nodeList[i];
    if (container.nodeType === Node.ELEMENT_NODE) {
      // Check if the container itself matches the selector
      if (container.matches(selector)) {
        return container;
      }

      // If not, search within the container
      const found = container.querySelector(selector);
      if (found) {
        return found;
      }
    }
  }

  return null; // No matching element found
};

export class InputNotFoundError extends Error {
  constructor(name) {
    super(`No input found with name "${name}"`);
    this.name = 'InputNotFoundError';
  }
}

export class BoundWidget {
  constructor(elementOrNodeList, name, parentCapabilities) {
    // look for an input element with the given name
    const selector = `:is(input,select,textarea,button)[name="${name}"]`;
    this.input = querySelectorIncludingSelf(elementOrNodeList, selector);
    if (!this.input) {
      throw new InputNotFoundError(name);
    }

    this.idForLabel = this.input.id;
    this.parentCapabilities = parentCapabilities || new Map();
  }

  getValue() {
    return this.input.value;
  }

  getState() {
    return this.input.value;
  }

  setState(state) {
    this.input.value = state;
  }

  setInvalid(invalid) {
    if (invalid) {
      this.input.setAttribute('aria-invalid', 'true');
    } else {
      this.input.removeAttribute('aria-invalid');
    }
  }

  getValueForLabel() {
    return this.getValue();
  }

  getTextLabel(opts) {
    const val = this.getValueForLabel();
    const allowedTypes = ['string', 'number', 'boolean'];
    if (!allowedTypes.includes(typeof val)) return null;
    const valString = String(val).trim();
    const maxLength = opts && opts.maxLength;
    if (maxLength && valString.length > maxLength) {
      return valString.substring(0, maxLength - 1) + '…';
    }
    return valString;
  }

  focus() {
    this.input.focus();
  }

  setCapabilityOptions(capability, options) {
    Object.assign(this.parentCapabilities.get(capability), options);
  }
}

export class Widget {
  constructor(html) {
    this.html = html;
  }

  boundWidgetClass = BoundWidget;

  render(
    placeholder,
    name,
    id,
    initialState,
    parentCapabilities,
    options = {},
  ) {
    const html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);

    /* write the HTML into a temp container to parse it into a node list */
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = html.trim();
    const childNodes = Array.from(tempContainer.childNodes);

    /* replace the placeholder with the new nodes */
    placeholder.replaceWith(...childNodes);

    const childElements = childNodes.filter(
      (node) => node.nodeType === Node.ELEMENT_NODE,
    );

    /* execute any scripts in the new element(s) */
    childElements.forEach((element) => {
      runInlineScripts(element);
    });

    // Add any extra attributes we received to the first element of the widget
    if (typeof options?.attributes === 'object') {
      setAttrs(childElements[0], options.attributes);
    }

    // eslint-disable-next-line new-cap
    const boundWidget = new this.boundWidgetClass(
      childElements.length === 1 ? childElements[0] : childNodes,
      name,
      parentCapabilities,
    );
    boundWidget.setState(initialState);
    return boundWidget;
  }

  getByName(name, container) {
    // eslint-disable-next-line new-cap
    return new this.boundWidgetClass(container, name);
  }
}

export class BoundCheckboxInput extends BoundWidget {
  getValue() {
    return this.input.checked;
  }

  getState() {
    return this.input.checked;
  }

  setState(state) {
    this.input.checked = state;
  }

  getValueForLabel() {
    return this.getValue() ? gettext('Yes') : gettext('No');
  }
}

export class CheckboxInput extends Widget {
  boundWidgetClass = BoundCheckboxInput;
}

export class BoundRadioSelect {
  constructor(element, name) {
    this.element = element;
    this.name = name;
    this.idForLabel = '';
    this.isMultiple = !!this.element.querySelector(
      `input[name="${name}"][type="checkbox"]`,
    );
    this.selector = `input[name="${name}"]:checked`;
  }

  getValueForLabel() {
    const getLabels = (input) => {
      const labels = Array.from(input?.labels || [])
        .map((label) => label.textContent.trim())
        .filter(Boolean);
      return labels.join(', ');
    };
    if (this.isMultiple) {
      return Array.from(this.element.querySelectorAll(this.selector))
        .map(getLabels)
        .join(', ');
    }
    return getLabels(this.element.querySelector(this.selector));
  }

  getTextLabel() {
    // This class does not extend BoundWidget, so we don't have the truncating
    // logic without duplicating the code here. Skip it for now.
    return this.getValueForLabel();
  }

  getValue() {
    if (this.isMultiple) {
      return Array.from(this.element.querySelectorAll(this.selector)).map(
        (el) => el.value,
      );
    }
    return this.element.querySelector(this.selector)?.value;
  }

  getState() {
    return Array.from(this.element.querySelectorAll(this.selector)).map(
      (el) => el.value,
    );
  }

  setState(state) {
    const inputs = this.element.querySelectorAll(`input[name="${this.name}"]`);
    for (let i = 0; i < inputs.length; i += 1) {
      inputs[i].checked = state.includes(inputs[i].value);
    }
  }

  setInvalid(invalid) {
    this.element
      .querySelectorAll(`input[name="${this.name}"]`)
      .forEach((input) => {
        if (invalid) {
          input.setAttribute('aria-invalid', 'true');
        } else {
          input.removeAttribute('aria-invalid');
        }
      });
  }

  focus() {
    this.element.querySelector(`input[name="${this.name}"]`)?.focus();
  }
}

export class RadioSelect extends Widget {
  boundWidgetClass = BoundRadioSelect;
}

export class BoundSelect extends BoundWidget {
  getValueForLabel() {
    return Array.from(this.input.selectedOptions)
      .map((option) => option.text)
      .join(', ');
  }

  getValue() {
    if (this.input.multiple) {
      return Array.from(this.input.selectedOptions).map(
        (option) => option.value,
      );
    }
    return this.input.value;
  }

  getState() {
    return Array.from(this.input.selectedOptions).map((option) => option.value);
  }

  setState(state) {
    const options = this.input.options;
    for (let i = 0; i < options.length; i += 1) {
      options[i].selected = state.includes(options[i].value);
    }
  }
}

export class Select extends Widget {
  boundWidgetClass = BoundSelect;
}

export class BlockWidget extends Widget {
  constructor() {
    // Pass an empty string as the HTML. This means we cannot generate new instances through `render`,
    // but we're not making use of that - and the real HTML would embed the block definition as a data
    // attribute, which could potentially be huge.
    super('');
  }

  render() {
    throw new Error('BlockWidget does not support rendering');
  }

  getByName(name, container) {
    // Retrieve the block object that was stashed on the root element by BlockController
    const rootElement = querySelectorIncludingSelf(container, `#${name}-root`);
    if (!rootElement) {
      throw new InputNotFoundError(name);
    }
    if (!rootElement.rootBlock) {
      throw new Error(
        `BlockWidget with name "${name}" does not have a root block attached.`,
      );
    }
    // The API for block objects matches the one for widgets (getValue, getState, etc.),
    // so we just return that in lieu of a BoundWidget.
    return rootElement.rootBlock;
  }
}
