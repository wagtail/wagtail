/* global $ */

import { escapeHtml as h } from '../../../utils/text';

export class StructBlockValidationError {
  constructor(blockErrors) {
    this.blockErrors = blockErrors;
  }
}

export class StructBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    const state = initialState || {};
    this.blockDef = blockDef;
    this.type = blockDef.name;

    this.childBlocks = {};

    if (blockDef.meta.formTemplate) {
      const html = blockDef.meta.formTemplate.replace(/__PREFIX__/g, prefix);
      const dom = $(html);
      $(placeholder).replaceWith(dom);
      this.blockDef.childBlockDefs.forEach((childBlockDef) => {
        const childBlockElement = dom
          .find('[data-structblock-child="' + childBlockDef.name + '"]')
          .get(0);
        const childBlock = childBlockDef.render(
          childBlockElement,
          prefix + '-' + childBlockDef.name,
          state[childBlockDef.name],
          initialError?.blockErrors[childBlockDef.name],
        );
        this.childBlocks[childBlockDef.name] = childBlock;
      });
    } else {
      const dom = $(`
        <div class="${h(this.blockDef.meta.classname || '')}">
        </div>
      `);
      $(placeholder).replaceWith(dom);

      if (this.blockDef.meta.helpText) {
        // help text is left unescaped as per Django conventions
        dom.append(`
          <span>
            <div class="help">
              ${this.blockDef.meta.helpIcon}
              ${this.blockDef.meta.helpText}
            </div>
          </span>
        `);
      }

      this.blockDef.childBlockDefs.forEach((childBlockDef) => {
        const childDom = $(`
          <div class="field ${
            childBlockDef.meta.required ? 'required' : ''
          }" data-contentpath="${childBlockDef.name}">
            <label class="field__label">${h(childBlockDef.meta.label)}</label>
            <div data-streamfield-block></div>
          </div>
        `);
        dom.append(childDom);
        const childBlockElement = childDom
          .find('[data-streamfield-block]')
          .get(0);
        const labelElement = childDom.find('label').get(0);
        const childBlock = childBlockDef.render(
          childBlockElement,
          prefix + '-' + childBlockDef.name,
          state[childBlockDef.name],
          initialError?.blockErrors[childBlockDef.name],
          new Map(),
        );

        this.childBlocks[childBlockDef.name] = childBlock;
        if (childBlock.idForLabel) {
          labelElement.setAttribute('for', childBlock.idForLabel);
        }
      });
    }
  }

  setState(state) {
    // eslint-disable-next-line guard-for-in
    for (const name in state) {
      this.childBlocks[name].setState(state[name]);
    }
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];

    for (const blockName in error.blockErrors) {
      if (error.blockErrors.hasOwnProperty(blockName)) {
        this.childBlocks[blockName].setError(error.blockErrors[blockName]);
      }
    }
  }

  getState() {
    const state = {};
    // eslint-disable-next-line guard-for-in
    for (const name in this.childBlocks) {
      state[name] = this.childBlocks[name].getState();
    }
    return state;
  }

  getValue() {
    const value = {};
    // eslint-disable-next-line guard-for-in
    for (const name in this.childBlocks) {
      value[name] = this.childBlocks[name].getValue();
    }
    return value;
  }

  getTextLabel(opts) {
    if (this.blockDef.meta.labelFormat) {
      /* use labelFormat - regexp replace any field references like '{first_name}'
      with the text label of that sub-block */
      return this.blockDef.meta.labelFormat.replace(
        /\{(\w+)\}/g,
        (tag, blockName) => {
          const block = this.childBlocks[blockName];
          if (block.getTextLabel) {
            /* to be strictly correct, we should be adjusting opts.maxLength to account for the overheads
          in the format string, and dividing the remainder across all the placeholders in the string,
          rather than just passing opts on to the child. But that would get complicated, and this is
          better than nothing... */
            return block.getTextLabel(opts);
          }
          return '';
        },
      );
    }

    /* if no labelFormat specified, just try each child block in turn until we find one that provides a label */
    for (const childDef of this.blockDef.childBlockDefs) {
      const child = this.childBlocks[childDef.name];
      if (child.getTextLabel) {
        const val = child.getTextLabel(opts);
        if (val) return val;
      }
    }
    // no usable label found
    return null;
  }

  focus(opts) {
    if (this.blockDef.childBlockDefs.length) {
      const firstChildName = this.blockDef.childBlockDefs[0].name;
      this.childBlocks[firstChildName].focus(opts);
    }
  }
}

export class StructBlockDefinition {
  constructor(name, childBlockDefs, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new StructBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}
