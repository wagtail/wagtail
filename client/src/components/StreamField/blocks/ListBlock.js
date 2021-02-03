import { BaseSequenceChild } from './BaseSequenceBlock';
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

export class ListBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(prefix)}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
        <button type="button" title="${h(this.blockDef.meta.strings.ADD)}" data-streamfield-list-add
            class="c-sf-add-button c-sf-add-button--visible">
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
      this.append(this.blockDef.initialChildState, { animate: true });
    });
  }

  clear() {
    this.countInput.val(0);
    this.listContainer.empty();
    this.children = [];
  }

  append(value, opts) {
    const index = this.children.length;
    const prefix = this.prefix + '-' + index;
    const placeholder = document.createElement('div');
    this.listContainer.append(placeholder);
    const animate = opts && opts.animate;

    const child = new ListChild(this.blockDef.childBlockDef, placeholder, prefix, index, null, value, {
      animate,
      onRequestDelete: (i) => { this.deleteBlock(i); },
      onRequestMoveUp: (i) => { this.moveBlock(i, i - 1); },
      onRequestMoveDown: (i) => { this.moveBlock(i, i + 1); },
      strings: this.blockDef.meta.strings,
    });
    this.children.push(child);
    this.countInput.val(this.children.length);

    const isFirstChild = (index === 0);
    /* isLastChild is always true for append, but we might as well get the logic for arbitrary
    insertions right... */
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
  }

  deleteBlock(index) {
    this.children[index].markDeleted({ animate: true });
    this.children.splice(index, 1);

    /* index numbers of children / menus above this index now need updating to match
    their array indexes */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i);
    }

    if (index === 0 && this.children.length > 0) {
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
    const childToMove = this.children[oldIndex];

    /* move HTML elements */
    if (newIndex > oldIndex) {
      $(childToMove.element).insertAfter(this.children[newIndex].element);
    } else {
      $(childToMove.element).insertBefore(this.children[newIndex].element);
    }

    /* reorder items in the `children` array */
    this.children.splice(oldIndex, 1);
    this.children.splice(newIndex, 0, childToMove);

    /* update index properties of moved items */
    if (newIndex > oldIndex) {
      for (let i = oldIndex; i <= newIndex; i++) {
        this.children[i].setIndex(i);
      }
    } else {
      for (let i = newIndex; i <= oldIndex; i++) {
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
