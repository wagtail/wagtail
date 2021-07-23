/* eslint-disable no-underscore-dangle */

import { BaseSequenceBlock, BaseSequenceChild, BaseInsertionControl } from './BaseSequenceBlock';
import { escapeHtml as h } from '../../../utils/text';

/* global $ */

export class ListBlockValidationError {
  constructor(blockErrors, nonBlockErrors) {
    this.blockErrors = blockErrors;
    this.nonBlockErrors = nonBlockErrors;
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
    const animate = opts && opts.animate;

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

    if (animate) {
      button.hide().slideDown();
    }
  }

  enable() {
    $(this.element).removeAttr('disabled');
  }

  disable() {
    $(this.element).attr('disabled', 'true');
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
    this.container = dom;
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

  _createChild(blockDef, placeholder, prefix, index, id, initialState, sequence, opts) {
    return new ListChild(blockDef, placeholder, prefix, index, id, initialState, sequence, opts);
  }

  _createInsertionControl(placeholder, opts) {
    return new InsertPosition(placeholder, opts);
  }

  /*
   * Called whenever a block is added or removed
   *
   * Updates the state of add / duplicate block buttons to prevent too many blocks being inserted.
   */
  blockCountChanged() {
    super.blockCountChanged();

    if (typeof this.blockDef.meta.maxNum === 'number') {
      if (this.children.length >= this.blockDef.meta.maxNum) {
        /* prevent adding new blocks */
        for (let i = 0; i < this.inserters.length; i++) {
          this.inserters[i].disable();
        }
        for (let i = 0; i < this.children.length; i++) {
          this.children[i].disableDuplication();
        }
      } else {
        /* allow adding new blocks */
        for (let i = 0; i < this.inserters.length; i++) {
          this.inserters[i].enable();
        }
        for (let i = 0; i < this.children.length; i++) {
          this.children[i].enableDuplication();
        }
      }
    }
  }

  insert(value, index, opts) {
    return this._insert(this.blockDef.childBlockDef, value, null, index, opts);
  }

  duplicateBlock(index, opts) {
    const child = this.children[index];
    const childState = child.getState();
    const animate = opts && opts.animate;
    this.insert(childState, index + 1, { animate, collapsed: child.collapsed });
    this.children[index + 1].focus({ soft: true });
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];

    // Non block errors
    const container = this.container[0];
    container.querySelectorAll(':scope > .help-block.help-critical').forEach(element => element.remove());

    if (error.nonBlockErrors.length > 0) {
      // Add a help block for each error raised
      error.nonBlockErrors.forEach(nonBlockError => {
        const errorElement = document.createElement('p');
        errorElement.classList.add('help-block');
        errorElement.classList.add('help-critical');
        errorElement.innerHTML = h(nonBlockError.messages[0]);
        container.insertBefore(errorElement, container.childNodes[0]);
      });
    }

    // error.blockErrors = a list with the same length as the data,
    // with nulls for items without errors
    error.blockErrors.forEach((blockError, blockIndex) => {
      if (blockError) {
        this.children[blockIndex].setError(blockError);
      }
    });
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
