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

    // See field.html for the reference implementation of this markup.
    const dom = $(`
      <div class="w-field__wrapper" data-field-wrapper>
        <div class="${h(this.blockDef.meta.classname)}" data-field>
          <div class="w-field__errors" id="${prefix}-errors" data-field-errors>
            <svg class="icon icon-warning w-field__errors-icon" aria-hidden="true" hidden><use href="#icon-warning"></use></svg>
          </div>
          <div class="w-field__input" data-field-input>
            <div data-streamfield-widget></div>
          </div>
          <div id="${prefix}-helptext" data-field-help></div>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    const widgetElement = dom.find('[data-streamfield-widget]').get(0);
    this.element = dom[0];
    this.field = this.element.querySelector('[data-field]');

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
      this.field.querySelector('[data-field-help]').appendChild(helpElement);
    }

    if (window.comments && this.blockDef.meta.showAddCommentButton) {
      const addCommentButtonElement = document.createElement('button');
      addCommentButtonElement.type = 'button';
      addCommentButtonElement.setAttribute(
        'aria-label',
        blockDef.meta.strings.ADD_COMMENT,
      );
      addCommentButtonElement.setAttribute('data-comment-add', '');
      addCommentButtonElement.classList.add(
        'w-field__comment-button',
        'w-field__comment-button--add',
        'u-hidden',
      );

      ReactDOM.render(
        <>
          <Icon name="comment-add" />
          <Icon name="comment-add-reversed" />
        </>,
        addCommentButtonElement,
      );
      this.field.classList.add('w-field--commentable');
      this.field
        .querySelector('[data-field-input]')
        .appendChild(addCommentButtonElement);
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
    const errors = this.field.querySelector('[data-field-errors]');

    errors
      .querySelectorAll('.error-message')
      .forEach((element) => element.remove());

    if (errorList) {
      this.field.classList.add('w-field--error');
      errors.querySelector('.icon').removeAttribute('hidden');

      const errorElement = document.createElement('p');
      errorElement.classList.add('error-message');
      errorElement.innerHTML = errorList
        .map((error) => `<span>${h(error.messages[0])}</span>`)
        .join('');
      errors.appendChild(errorElement);
    } else {
      this.field.classList.remove('w-field--error');
      errors.querySelector('.icon').setAttribute('hidden', 'true');
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
