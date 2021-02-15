/* eslint-disable no-underscore-dangle */

import { BaseSequenceBlock, BaseSequenceChild, BaseInsertionControl } from './BaseSequenceBlock';
import { escapeHtml as h } from '../../../utils/text';

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

class InsertPosition extends BaseInsertionControl {
  /*
  Represents a position in the DOM where a new list item can be inserted.

  This renders a + button. Later, these could also be used to represent drop zones for drag+drop reordering.
  */
  constructor(placeholder, opts) {
    super(placeholder, opts);
    this.onRequestInsert = opts && opts.onRequestInsert;

    const button = $(`
      <button type="button" title="${h(opts.strings.ADD)}" data-streamfield-list-add
          class="c-sf-add-button c-sf-add-button--visible">
        <i aria-hidden="true">+</i>
      </button>
    `);
    $(placeholder).replaceWith(button);
    this.element = button.get(0);

    button.click(() => {
      if (this.onRequestInsert) {
        this.onRequestInsert(this.index);
      }
    });
  }
}

export class ListBlock extends BaseSequenceBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(prefix)}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
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
    this.inserters = [];
    this.blockCounter = 0;
    this.countInput = dom.find('[data-streamfield-list-count]');
    this.sequenceContainer = dom.find('[data-streamfield-list-container]');
    this.setState(initialState || []);

    if (initialError) {
      this.setError(initialError);
    }
  }

  _getChildDataForInsertion() {
    /* Called when an 'insert new block' action is triggered: given a dict of data from the insertion control,
    return the block definition and initial state to be used for the new block.
    For a ListBlock, no data is passed from the insertion control, as there is a single fixed child block definition.
    */
    const blockDef = this.blockDef.childBlockDef;
    const initialState = this.blockDef.initialChildState;
    return [blockDef, initialState];
  }

  _createChild(blockDef, placeholder, prefix, index, id, initialState, opts) {
    return new ListChild(blockDef, placeholder, prefix, index, id, initialState, opts);
  }

  _createInsertionControl(placeholder, opts) {
    return new InsertPosition(placeholder, opts);
  }

  insert(value, index, opts) {
    return this._insert(this.blockDef.childBlockDef, value, null, index, opts);
  }

  duplicateBlock(index) {
    const childState = this.children[index].getState();
    this.insert(childState, index + 1, { animate: true });
    this.children[index + 1].focus({ soft: true });
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
