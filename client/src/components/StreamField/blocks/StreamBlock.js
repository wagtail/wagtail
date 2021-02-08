/* eslint-disable no-underscore-dangle */

import { BaseSequenceChild, BaseInsertionControl } from './BaseSequenceBlock';
import { escapeHtml as h } from '../../../utils/text';

/* global $ */

export class StreamBlockValidationError {
  constructor(nonBlockErrors, blockErrors) {
    this.nonBlockErrors = nonBlockErrors;
    this.blockErrors = blockErrors;
  }
}

class StreamChild extends BaseSequenceChild {
  /*
  wrapper for a block inside a StreamBlock, handling StreamBlock-specific metadata
  such as id
  */
  getState() {
    return {
      type: this.type,
      value: this.block.getState(),
      id: this.id,
    };
  }

  getValue() {
    return {
      type: this.type,
      value: this.block.getValue(),
      id: this.id,
    };
  }
}

class StreamBlockMenu extends BaseInsertionControl {
  constructor(placeholder, opts) {
    super(placeholder, opts);
    this.groupedChildBlockDefs = opts.groupedChildBlockDefs;

    const dom = $(`
      <div>
        <button data-streamblock-menu-open type="button" title="${h(opts.strings.ADD)}"
            class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
        <div data-streamblock-menu-outer>
          <div data-streamblock-menu-inner class="c-sf-add-panel"></div>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);

    this.addButton = dom.find('[data-streamblock-menu-open]');
    this.addButton.click(() => {
      this.toggle();
    });

    this.outerContainer = dom.find('[data-streamblock-menu-outer]');
    this.innerContainer = dom.find('[data-streamblock-menu-inner]');
    this.hasRenderedMenu = false;
    this.isOpen = false;
    this.close({ animate: false });
  }

  renderMenu() {
    if (this.hasRenderedMenu) return;
    this.hasRenderedMenu = true;

    this.groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      if (group) {
        const heading = $('<h4 class="c-sf-add-panel__group-title"></h4>').text(group);
        this.innerContainer.append(heading);
      }
      const grid = $('<div class="c-sf-add-panel__grid"></div>');
      this.innerContainer.append(grid);
      blockDefs.forEach(blockDef => {
        const button = $(`
          <button type="button" class="c-sf-button action-add-block-${h(blockDef.name)}">
            <span class="c-sf-button__icon">
              <i class="icon icon-${h(blockDef.meta.icon)}"></i>
            </span>
            <span class="c-sf-button__label">${h(blockDef.meta.label)}</span>
          </button>
        `);
        grid.append(button);
        button.click(() => {
          if (this.onRequestInsert) {
            this.onRequestInsert(this.index, { type: blockDef.name });
          }
          this.close({ animate: true });
        });
      });
    });
  }

  toggle() {
    if (this.isOpen) {
      this.close({ animate: true });
    } else {
      this.open({ animate: true });
    }
  }
  open(opts) {
    this.renderMenu();
    if (opts && opts.animate) {
      this.outerContainer.slideDown();
    } else {
      this.outerContainer.show();
    }
    this.addButton.addClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'false');
    this.isOpen = true;
  }
  close(opts) {
    if (opts && opts.animate) {
      this.outerContainer.slideUp();
    } else {
      this.outerContainer.hide();
    }
    this.addButton.removeClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'true');
    this.isOpen = false;
  }
}

export class StreamBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(prefix)}-count" data-streamfield-stream-count value="0">
        <div data-streamfield-stream-container></div>
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

    // StreamChild objects for the current (non-deleted) child blocks
    this.children = [];

    // Insertion control objects - there are one more of these than there are children.
    // The control at index n will insert a block at index n
    this.inserters = [];

    // Incrementing counter used to generate block prefixes, also reflected in the
    // 'count' hidden input. This count includes deleted items
    this.blockCounter = 0;
    this.countInput = dom.find('[data-streamfield-stream-count]');

    // Parent element of insert control and block elements (potentially including deleted items,
    // which are left behind as hidden elements with a '-deleted' input so that the
    // server-side form handler knows to skip it)
    this.streamContainer = dom.find('[data-streamfield-stream-container]');
    this.setState(initialState || []);
    this.container = dom;

    if (initialError) {
      this.setError(initialError);
    }
  }

  clear() {
    this.countInput.val(0);
    this.streamContainer.empty();
    this.children = [];
    this.blockCounter = 0;

    const placeholder = document.createElement('div');
    this.streamContainer.append(placeholder);
    this.inserters = [
      this._createInsertionControl(
        placeholder, {
          index: 0,
          onRequestInsert: (index, opts) => {
            this._onRequestInsert(index, opts);
          },
          strings: this.blockDef.meta.strings,
        }
      )
    ];
  }

  _createChild(blockDef, placeholder, prefix, index, id, initialState, opts) {
    return new StreamChild(blockDef, placeholder, prefix, index, id, initialState, opts);
  }

  _createInsertionControl(placeholder, opts) {
    // eslint-disable-next-line no-param-reassign
    opts.groupedChildBlockDefs = this.blockDef.groupedChildBlockDefs;
    return new StreamBlockMenu(placeholder, opts);
  }

  insert({ type, value, id }, index, opts) {
    const childBlockDef = this.blockDef.childBlockDefsByName[type];
    return this._insert(childBlockDef, value, id, index, opts);
  }

  _insert(childBlockDef, initialState, id, index, opts) {
    const prefix = this.prefix + '-' + this.blockCounter;
    const animate = opts && opts.animate;
    this.blockCounter++;

    /*
    a new inserter and block will be inserted AFTER the inserter with the given index;
    e.g if there are 3 blocks the children of streamContainer will be
    [inserter 0, block 0, inserter 1, block 1, inserter 2, block 2, inserter 3]
    and inserting a new block at index 1 will create a new block 1 and inserter 2 after the
    current inserter 1, and increment everything after that point
    */
    const existingMenuElement = this.inserters[index].element;
    const blockPlaceholder = document.createElement('div');
    const inserterPlaceholder = document.createElement('div');
    $(blockPlaceholder).insertAfter(existingMenuElement);
    $(inserterPlaceholder).insertAfter(blockPlaceholder);

    /* shuffle up indexes of all blocks / inserters above this index */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i + 1);
    }
    for (let i = index + 1; i < this.inserters.length; i++) {
      this.inserters[i].setIndex(i + 1);
    }

    const child = this._createChild(childBlockDef, blockPlaceholder, prefix, index, id, initialState, {
      animate,
      onRequestDuplicate: (i) => { this.duplicateBlock(i); },
      onRequestDelete: (i) => { this.deleteBlock(i); },
      onRequestMoveUp: (i) => { this.moveBlock(i, i - 1); },
      onRequestMoveDown: (i) => { this.moveBlock(i, i + 1); },
      strings: this.blockDef.meta.strings,
    });
    this.children.splice(index, 0, child);

    const inserter = this._createInsertionControl(
      inserterPlaceholder, {
        index: index + 1,
        onRequestInsert: (newIndex, inserterOpts) => {
          this._onRequestInsert(newIndex, inserterOpts);
        },
        strings: this.blockDef.meta.strings,
      }
    );
    this.inserters.splice(index + 1, 0, inserter);

    this.countInput.val(this.blockCounter);

    const isFirstChild = (index === 0);
    const isLastChild = (index === this.children.length - 1);
    if (!isFirstChild) {
      child.enableMoveUp();
      if (isLastChild) {
        /* previous child (which was previously the last one) can now move down */
        this.children[index - 1].enableMoveDown();
      }
    }
    if (!isLastChild) {
      child.enableMoveDown();
      if (isFirstChild) {
        /* next child (which was previously the first one) can now move up */
        this.children[index + 1].enableMoveUp();
      }
    }

    return child;
  }

  _getChildDataForInsertion({ type }) {
    /* Called when an 'insert new block' action is triggered: given a dict of data from the insertion control,
    return the block definition and initial state to be used for the new block.
    For a StreamBlock, the dict of data consists of 'type' (the chosen block type name, as a string).
    */
    const blockDef = this.blockDef.childBlockDefsByName[type];
    const initialState = this.blockDef.initialChildStates[type];
    return [blockDef, initialState];
  }

  _onRequestInsert(index, opts) {
    /* handler for an 'insert new block' action */
    const [blockDef, initialState] = this._getChildDataForInsertion(opts);
    const newChild = this._insert(blockDef, initialState, null, index, { animate: true });
    newChild.focus();
  }

  duplicateBlock(index) {
    const childState = this.children[index].getState();
    childState.id = null;
    this.insert(childState, index + 1, { animate: true });
    this.children[index + 1].focus();
  }

  deleteBlock(index) {
    this.children[index].markDeleted({ animate: true });
    this.inserters[index].delete();
    this.children.splice(index, 1);
    this.inserters.splice(index, 1);

    /* index numbers of children / inserters above this index now need updating to match
    their array indexes */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i);
    }
    for (let i = index; i < this.inserters.length; i++) {
      this.inserters[i].setIndex(i);
    }

    if (index === 0  && this.children.length > 0) {
      /* we have removed the first child; the new first child cannot be moved up */
      this.children[0].disableMoveUp();
    }
    if (index === this.children.length && this.children.length > 0) {
      /* we have removed the last child; the new last child cannot be moved down */
      this.children[this.children.length - 1].disableMoveDown();
    }
  }

  moveBlock(oldIndex, newIndex) {
    if (oldIndex === newIndex) return;
    const inserterToMove = this.inserters[oldIndex];
    const childToMove = this.children[oldIndex];

    /* move HTML elements */
    if (newIndex > oldIndex) {
      $(inserterToMove.element).insertAfter(this.children[newIndex].element);
    } else {
      $(inserterToMove.element).insertBefore(this.inserters[newIndex].element);
    }
    $(childToMove.element).insertAfter(inserterToMove.element);

    /* reorder items in the `inserters` and `children` arrays */
    this.inserters.splice(oldIndex, 1);
    this.inserters.splice(newIndex, 0, inserterToMove);
    this.children.splice(oldIndex, 1);
    this.children.splice(newIndex, 0, childToMove);

    /* update index properties of moved items */
    if (newIndex > oldIndex) {
      for (let i = oldIndex; i <= newIndex; i++) {
        this.inserters[i].setIndex(i);
        this.children[i].setIndex(i);
      }
    } else {
      for (let i = newIndex; i <= oldIndex; i++) {
        this.inserters[i].setIndex(i);
        this.children[i].setIndex(i);
      }
    }

    /* enable/disable up/down arrows as required */
    const maxIndex = this.children.length - 1;
    if (oldIndex === 0) {
      childToMove.enableMoveUp();
      this.children[0].disableMoveUp();
    }
    if (oldIndex === maxIndex) {
      childToMove.enableMoveDown();
      this.children[maxIndex].disableMoveDown();
    }
    if (newIndex === 0) {
      childToMove.disableMoveUp();
      this.children[1].enableMoveUp();
    }
    if (newIndex === maxIndex) {
      childToMove.disableMoveDown();
      this.children[maxIndex - 1].enableMoveDown();
    }
  }

  setState(values) {
    this.clear();
    values.forEach((val, i) => {
      this.insert(val, i);
    });
    if (values.length === 0) {
      /* for an empty list, begin with the menu open */
      this.inserters[0].open({ animate: false });
    }
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];

    // Non block errors
    const container = this.container[0];
    container.querySelectorAll(':scope > .help-block .help-critical').forEach(element => element.remove());

    if (error.nonBlockErrors.length > 0) {
      // Add a help block for each error raised
      error.nonBlockErrors.forEach(errorText => {
        const errorElement = document.createElement('p');
        errorElement.classList.add('help-block');
        errorElement.classList.add('help-critical');
        errorElement.innerText = errorText;
        container.insertBefore(errorElement, container.childNodes[0]);
      });
    }

    // Block errors
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

export class StreamBlockDefinition {
  constructor(name, groupedChildBlockDefs, initialChildStates, meta) {
    this.name = name;
    this.groupedChildBlockDefs = groupedChildBlockDefs;
    this.initialChildStates = initialChildStates;
    this.childBlockDefsByName = {};
    // eslint-disable-next-line no-unused-vars
    this.groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      blockDefs.forEach(blockDef => {
        this.childBlockDefsByName[blockDef.name] = blockDef;
      });
    });
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new StreamBlock(this, placeholder, prefix, initialState, initialError);
  }
}
