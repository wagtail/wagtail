/* global $ */

import { escapeHtml as h } from '../../../utils/text';

export class FieldBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;

    const dom = $(`
      <div class="${h(this.blockDef.meta.classname)}">
        <div class="field-content">
          <div class="input">
            <div data-streamfield-widget></div>
            <span></span>
          </div>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    const widgetElement = dom.find('[data-streamfield-widget]').get(0);
    this.element = dom[0];

    try {
      this.widget = this.blockDef.widget.render(widgetElement, prefix, prefix, initialState);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
      this.setError([
        ['This widget failed to render, please check the console for details']
      ]);
      return;
    }

    this.idForLabel = this.widget.idForLabel;

    if (this.blockDef.meta.helpText) {
      const helpElement = document.createElement('p');
      helpElement.classList.add('help');
      helpElement.innerHTML = this.blockDef.meta.helpText;  // unescaped, as per Django conventions
      this.element.querySelector('.field-content').appendChild(helpElement);
    }

    if (initialError) {
      this.setError(initialError);
    }
  }

  setState(state) {
    if (this.widget) {
      this.widget.setState(state);
    }
  }

  setError(errorList) {
    this.element.querySelectorAll(':scope > .field-content > .error-message').forEach(element => element.remove());

    if (errorList) {
      this.element.classList.add('error');

      const errorElement = document.createElement('p');
      errorElement.classList.add('error-message');
      errorElement.innerHTML = errorList.map(error => `<span>${h(error[0])}</span>`).join('');
      this.element.querySelector('.field-content').appendChild(errorElement);
    } else {
      this.element.classList.remove('error');
    }
  }

  getState() {
    return this.widget.getState();
  }

  getValue() {
    return this.widget.getValue();
  }

  focus(opts) {
    if (this.widget) {
      this.widget.focus(opts);
    }
  }
}

export class FieldBlockDefinition {
  constructor(name, widget, meta) {
    this.name = name;
    this.widget = widget;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new FieldBlock(this, placeholder, prefix, initialState, initialError);
  }
}
