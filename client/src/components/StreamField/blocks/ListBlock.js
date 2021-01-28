import { BaseSequenceChild } from './BaseSequenceBlock';

/* global $ */

export class ListBlockValidationError {
  constructor(blockErrors) {
    this.blockErrors = blockErrors;
  }
}

class ListChild extends BaseSequenceChild {
  /*
  wrapper for an item inside a ListBlock
  */
  getState() {
    return this.block.getState();
  }

  getValue() {
    return this.block.getValue();
  }
}

export class ListBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${this.blockDef.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
        <button type="button" title="Add" data-streamfield-list-add class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    if (this.blockDef.meta.helpText) {
      // help text is left unescaped as per Django conventions
      $(`
        <span>
          <div class="help">
            ${this.blockDef.meta.helpIcon}
            ${this.blockDef.meta.helpText}
          </div>
        </span>
      `).insertBefore(dom);
    }

    this.children = [];
    this.countInput = dom.find('[data-streamfield-list-count]');
    this.listContainer = dom.find('[data-streamfield-list-container]');
    this.setState(initialState || []);

    if (initialError) {
      this.setError(initialError);
    }

    dom.find('button[data-streamfield-list-add]').click(() => {
      this.append(this.blockDef.initialChildState);
    });
  }

  clear() {
    this.countInput.val(0);
    this.listContainer.empty();
    this.children = [];
  }

  append(value) {
    const index = this.children.length;
    const prefix = this.prefix + '-' + index;
    const placeholder = document.createElement('div');
    this.listContainer.append(placeholder);

    const child = new ListChild(this.blockDef.childBlockDef, placeholder, prefix, index, null, value, {
      onRequestDelete: (i) => { this.deleteBlock(i); }
    });
    this.children.push(child);
    this.countInput.val(this.children.length);
  }

  deleteBlock(index) {
    this.children[index].markDeleted({ animate: true });
    this.children.splice(index, 1);

    /* index numbers of children / menus above this index now need updating to match
    their array indexes */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i);
    }
  }

  setState(values) {
    this.clear();
    values.forEach(val => {
      this.append(val);
    });
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];

    // eslint-disable-next-line no-restricted-syntax
    for (const blockIndex in error.blockErrors) {
      if (error.blockErrors.hasOwnProperty(blockIndex)) {
        this.children[blockIndex].setError(error.blockErrors[blockIndex]);
      }
    }
  }

  getState() {
    return this.children.map(child => child.getState());
  }

  getValue() {
    return this.children.map(child => child.getValue());
  }

  focus() {
    if (this.children.length) {
      this.children[0].focus();
    }
  }
}

export class ListBlockDefinition {
  constructor(name, childBlockDef, initialChildState, meta) {
    this.name = name;
    this.childBlockDef = childBlockDef;
    this.initialChildState = initialChildState;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new ListBlock(this, placeholder, prefix, initialState, initialError);
  }
}
