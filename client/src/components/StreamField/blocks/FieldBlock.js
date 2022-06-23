/* global $ */
import ReactDOM from 'react-dom';
import React from 'react';
import { escapeHtml as h } from '../../../utils/text';
import Icon from '../../Icon/Icon';

export class FieldBlock {
  constructor(
    blockDef,
    placeholder,
    prefix,
    initialState,
    initialError,
    parentCapabilities,
  ) {
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

    this.parentCapabilities = parentCapabilities || new Map();

    this.prefix = prefix;

    try {
      this.widget = this.blockDef.widget.render(
        widgetElement,
        prefix,
        prefix,
        initialState,
        this.parentCapabilities,
      );
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
      this.setError([
        {
          messages: [
            'This widget failed to render, please check the console for details',
          ],
        },
      ]);
      return;
    }

    this.idForLabel = this.widget.idForLabel;

    if (this.blockDef.meta.helpText) {
      const helpElement = document.createElement('p');
      helpElement.classList.add('help');
      helpElement.innerHTML = this.blockDef.meta.helpText; // unescaped, as per Django conventions
      this.element.querySelector('.field-content').appendChild(helpElement);
    }

    if (window.comments && this.blockDef.meta.showAddCommentButton) {
      const fieldCommentControlElement = document.createElement('div');
      fieldCommentControlElement.classList.add('field-comment-control');
      this.element.appendChild(fieldCommentControlElement);

      const addCommentButtonElement = document.createElement('button');
      addCommentButtonElement.type = 'button';
      addCommentButtonElement.setAttribute(
        'aria-label',
        blockDef.meta.strings.ADD_COMMENT,
      );
      addCommentButtonElement.setAttribute('data-comment-add', '');
      addCommentButtonElement.classList.add('button');
      addCommentButtonElement.classList.add('button-secondary');
      addCommentButtonElement.classList.add('button-small');
      addCommentButtonElement.classList.add('u-hidden');

      ReactDOM.render(
        <>
          <Icon name="comment-add" className="icon-default" />
          <Icon name="comment-add-reversed" className="icon-reversed" />
        </>,
        addCommentButtonElement,
      );
      fieldCommentControlElement.appendChild(addCommentButtonElement);
      window.comments.initAddCommentButton(addCommentButtonElement);
    }

    if (initialError) {
      this.setError(initialError);
    }
  }

  setCapabilityOptions(capability, options) {
    Object.assign(this.parentCapabilities.get(capability), options);
    if (this.widget && this.widget.setCapabilityOptions) {
      this.widget.setCapabilityOptions(capability, options);
    }
  }

  setState(state) {
    if (this.widget) {
      this.widget.setState(state);
    }
  }

  setError(errorList) {
    this.element
      .querySelectorAll(':scope > .field-content > .error-message')
      .forEach((element) => element.remove());

    if (errorList) {
      this.element.classList.add('error');

      const errorElement = document.createElement('p');
      errorElement.classList.add('error-message');
      errorElement.innerHTML = errorList
        .map((error) => `<span>${h(error.messages[0])}</span>`)
        .join('');
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

  render(placeholder, prefix, initialState, initialError, parentCapabilities) {
    return new FieldBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
      parentCapabilities,
    );
  }
}
