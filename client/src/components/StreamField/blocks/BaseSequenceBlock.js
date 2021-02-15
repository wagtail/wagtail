/* eslint-disable no-underscore-dangle */

/* global $ */

import { escapeHtml as h } from '../../../utils/text';

export class BaseSequenceChild {
  constructor(blockDef, placeholder, prefix, index, id, initialState, opts) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;

    const animate = opts && opts.animate;
    this.onRequestDuplicate = opts && opts.onRequestDuplicate;
    this.onRequestDelete = opts && opts.onRequestDelete;
    this.onRequestMoveUp = opts && opts.onRequestMoveUp;
    this.onRequestMoveDown = opts && opts.onRequestMoveDown;
    const strings = (opts && opts.strings) || {};

    const dom = $(`
      <div aria-hidden="false">
        <input type="hidden"  name="${this.prefix}-deleted" value="">
        <input type="hidden" name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${h(this.type || '')}">
        <input type="hidden" name="${this.prefix}-id" value="${h(this.id || '')}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${h(this.blockDef.meta.icon)}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type">${h(this.blockDef.meta.label)}</span>
                  <button type="button" data-move-up-button class="c-sf-block__actions__single"
                      disabled title="${h(strings.MOVE_UP)}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-move-down-button class="c-sf-block__actions__single"
                      disabled title="${h(strings.MOVE_DOWN)}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-duplicate-button
                      class="c-sf-block__actions__single" title="${h(strings.DUPLICATE)}">
                    <i class="icon icon-duplicate" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-delete-button
                      class="c-sf-block__actions__single" title="${h(strings.DELETE)}">
                    <i class="icon icon-bin" aria-hidden="true"></i>
                  </button>
                </div>
              </div>
              <div class="c-sf-block__content" aria-hidden="false">
                <div class="c-sf-block__content-inner">
                  <div data-streamfield-block></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `);

    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);
    const blockElement = dom.find('[data-streamfield-block]').get(0);

    this.duplicateButton = dom.find('button[data-duplicate-button]');
    this.duplicateButton.click(() => {
      if (this.onRequestDuplicate) this.onRequestDuplicate(this.index);
    });

    dom.find('button[data-delete-button]').click(() => {
      if (this.onRequestDelete) this.onRequestDelete(this.index);
    });

    this.deletedInput = dom.find(`input[name="${this.prefix}-deleted"]`);
    this.indexInput = dom.find(`input[name="${this.prefix}-order"]`);

    this.moveUpButton = dom.find('button[data-move-up-button]');
    this.moveUpButton.click(() => {
      if (this.onRequestMoveUp) this.onRequestMoveUp(this.index);
    });
    this.moveDownButton = dom.find('button[data-move-down-button]');
    this.moveDownButton.click(() => {
      if (this.onRequestMoveDown) this.onRequestMoveDown(this.index);
    });

    this.block = this.blockDef.render(blockElement, this.prefix + '-value', initialState);

    if (animate) {
      dom.hide().slideDown();
    }
  }

  markDeleted({ animate = false }) {
    this.deletedInput.val('1');
    if (animate) {
      $(this.element).slideUp().dequeue()
        .fadeOut()
        .attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }
  }

  enableDuplication() {
    this.duplicateButton.removeAttr('disabled');
  }
  disableDuplication() {
    this.duplicateButton.attr('disabled', 'true');
  }
  enableMoveUp() {
    this.moveUpButton.removeAttr('disabled');
  }
  disableMoveUp() {
    this.moveUpButton.attr('disabled', 'true');
  }
  enableMoveDown() {
    this.moveDownButton.removeAttr('disabled');
  }
  disableMoveDown() {
    this.moveDownButton.attr('disabled', 'true');
  }

  setIndex(newIndex) {
    this.index = newIndex;
    this.indexInput.val(newIndex);
  }

  setError(error) {
    this.block.setError(error);
  }

  focus(opts) {
    this.block.focus(opts);
  }
}

export class BaseInsertionControl {
  /* Base class for controls that appear between blocks in a sequence, to allow inserting new
  blocks at that point. Subclasses should render an HTML structure with a single root element
  (replacing the placeholder passed to the constructor) and set it as this.element.
  When the user requests to insert a block, we call onRequestInsert passing the index number
  and a dict of control-specific options. */
  constructor(placeholder, opts) {
    this.index = opts && opts.index;
    this.onRequestInsert = opts && opts.onRequestInsert;
  }

  setIndex(newIndex) {
    this.index = newIndex;
  }

  delete() {
    $(this.element).hide().attr('aria-hidden', 'true');
  }
}


export class BaseSequenceBlock {
  // eslint-disable-next-line no-unused-vars
  _createChild(blockDef, placeholder, prefix, index, id, initialState, opts) {
    throw new Error('not implemented');
  }

  // eslint-disable-next-line no-unused-vars
  _createInsertionControl(placeholder, opts) {
    throw new Error('not implemented');
  }

  // eslint-disable-next-line no-unused-vars
  _getChildDataForInsertion(opts) {
    throw new Error('not implemented');
  }

  clear() {
    this.countInput.val(0);
    this.sequenceContainer.empty();
    this.children = [];
    this.blockCounter = 0;

    // Create initial insertion control
    const placeholder = document.createElement('div');
    this.sequenceContainer.append(placeholder);
    this.inserters = [
      this._createInsertionControl(
        placeholder, {
          index: 0,
          onRequestInsert: (newIndex, opts) => {
            this._onRequestInsert(newIndex, opts);
          },
          strings: this.blockDef.meta.strings,
        }
      )
    ];
  }

  _onRequestInsert(index, opts) {
    /* handler for an 'insert new block' action */
    const [blockDef, initialState] = this._getChildDataForInsertion(opts);
    const newChild = this._insert(blockDef, initialState, null, index, { animate: true });
    // focus the newly added field if we can do so without obtrusive UI behaviour
    newChild.focus({ soft: true });
  }


  _insert(childBlockDef, initialState, id, index, opts) {
    const prefix = this.prefix + '-' + this.blockCounter;
    const animate = opts && opts.animate;
    this.blockCounter++;

    /*
    a new inserter and block will be inserted AFTER the inserter with the given index;
    e.g if there are 3 blocks the children of sequenceContainer will be
    [inserter 0, block 0, inserter 1, block 1, inserter 2, block 2, inserter 3]
    and inserting a new block at index 1 will create a new block 1 and inserter 2 after the
    current inserter 1, and increment everything after that point
    */
    const existingInserterElement = this.inserters[index].element;
    const blockPlaceholder = document.createElement('div');
    const inserterPlaceholder = document.createElement('div');
    $(blockPlaceholder).insertAfter(existingInserterElement);
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
  }

  getState() {
    return this.children.map(child => child.getState());
  }

  getValue() {
    return this.children.map(child => child.getValue());
  }

  focus(opts) {
    if (this.children.length) {
      this.children[0].focus(opts);
    }
  }
}
