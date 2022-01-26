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
        { messages: ['This widget failed to render, please check the console for details'] }
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

    if (window.comments && this.blockDef.meta.showAddCommentButton) {
      const fieldCommentControlElement = document.createElement('div');
      fieldCommentControlElement.classList.add('field-comment-control');
      this.element.appendChild(fieldCommentControlElement);

      const addCommentButtonElement = document.createElement('button');
      addCommentButtonElement.type = 'button';
      addCommentButtonElement.setAttribute('aria-label', blockDef.meta.strings.ADD_COMMENT);
      addCommentButtonElement.setAttribute('data-comment-add', '');
      addCommentButtonElement.classList.add('button');
      addCommentButtonElement.classList.add('button-secondary');
      addCommentButtonElement.classList.add('button-small');
      addCommentButtonElement.classList.add('u-hidden');
      addCommentButtonElement.innerHTML = (
        '<svg class="icon icon-comment-add initial icon-default" aria-hidden="true" focusable="false">'
        + '<use href="#icon-comment-add"></use></svg>'
        + '<svg class="icon icon-comment-add initial icon-reversed" aria-hidden="true" focusable="false">'
        + '<use href="#icon-comment-add-reversed"></use></svg>'
      );
      fieldCommentControlElement.appendChild(addCommentButtonElement);
      window.comments.initAddCommentButton(addCommentButtonElement);
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
      errorElement.innerHTML = errorList.map(error => `<span>${h(error.messages[0])}</span>`).join('');
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

  getTextLabel(opts) {
    if (this.widget.getTextLabel) {
      return this.widget.getTextLabel(opts);
    }
    return null;
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
