/* eslint-disable no-underscore-dangle */

/* global $ */

import EventEmitter from 'events';
import { escapeHtml as h } from '../../../utils/text';

class ActionButton {
  constructor(sequenceChild) {
    this.sequenceChild = sequenceChild;
  }

  render(container) {
    const label =
      this.sequenceChild.strings[this.labelIdentifier] || this.labelIdentifier;

    this.dom = $(`
      <button type="button" class="c-sf-block__actions__single" title="${h(
        label,
      )}">
        <svg class="icon icon-${h(this.icon)}" aria-hidden="true">
          <use href="#icon-${h(this.icon)}"></use>
        </svg>
      </button>
    `);

    this.dom.on('click', () => {
      if (this.onClick) this.onClick();
      return false; // don't propagate to header's onclick event (which collapses the block)
    });

    $(container).append(this.dom);

    if (this.enableEvent) {
      this.sequenceChild.on(this.enableEvent, () => {
        this.enable();
      });
    }

    if (this.disableEvent) {
      this.sequenceChild.on(this.disableEvent, () => {
        this.disable();
      });
    }

    if (this.initiallyDisabled) {
      this.disable();
    }
  }

  enable() {
    this.dom.removeAttr('disabled');
  }

  disable() {
    this.dom.attr('disabled', 'true');
  }
}

class MoveUpButton extends ActionButton {
  enableEvent = 'enableMoveUp';
  disableEvent = 'disableMoveUp';
  initiallyDisabled = true;
  icon = 'arrow-up';
  labelIdentifier = 'MOVE_UP';

  onClick() {
    this.sequenceChild.moveUp();
  }
}

class MoveDownButton extends ActionButton {
  enableEvent = 'enableMoveDown';
  disableEvent = 'disableMoveDown';
  initiallyDisabled = true;
  icon = 'arrow-down';
  labelIdentifier = 'MOVE_DOWN';

  onClick() {
    this.sequenceChild.moveDown();
  }
}

class DuplicateButton extends ActionButton {
  enableEvent = 'enableDuplication';
  disableEvent = 'disableDuplication';
  icon = 'duplicate';
  labelIdentifier = 'DUPLICATE';

  onClick() {
    this.sequenceChild.duplicate({ animate: true });
  }
}

class DeleteButton extends ActionButton {
  icon = 'bin';
  labelIdentifier = 'DELETE';

  onClick() {
    this.sequenceChild.delete({ animate: true });
  }
}

export class BaseSequenceChild extends EventEmitter {
  constructor(
    blockDef,
    placeholder,
    prefix,
    index,
    id,
    initialState,
    sequence,
    opts,
  ) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;
    this.sequence = sequence;

    const animate = opts && opts.animate;
    this.collapsed = opts && opts.collapsed;
    this.strings = (opts && opts.strings) || {};

    const dom = $(`
      <div aria-hidden="false" ${
        this.id
          ? `data-contentpath="${h(this.id)}"`
          : 'data-contentpath-disabled'
      }>
        <input type="hidden"  name="${this.prefix}-deleted" value="">
        <input type="hidden" name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${h(
      this.type || '',
    )}">
        <input type="hidden" name="${this.prefix}-id" value="${h(
      this.id || '',
    )}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div data-block-header class="c-sf-block__header c-sf-block__header--collapsible">
                <svg class="icon icon-${h(
                  this.blockDef.meta.icon,
                )} c-sf-block__header__icon" aria-hidden="true">
                  <use href="#icon-${h(this.blockDef.meta.icon)}"></use>
                </svg>
                <h3 data-block-title class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions" data-block-actions>
                  <span class="c-sf-block__type">${h(
                    this.blockDef.meta.label,
                  )}</span>
                </div>
              </div>
              <div data-block-content class="c-sf-block__content" aria-hidden="false">
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
    this.actionsContainerElement = dom.find('[data-block-actions]').get(0);
    this.titleElement = dom.find('[data-block-title]');
    this.contentElement = dom.find('[data-block-content]');
    this.deletedInput = dom.find(`input[name="${this.prefix}-deleted"]`);
    this.indexInput = dom.find(`input[name="${this.prefix}-order"]`);

    dom.find('[data-block-header]').click(() => {
      this.toggleCollapsedState();
    });

    this.addActionButton(new MoveUpButton(this));
    this.addActionButton(new MoveDownButton(this));
    this.addActionButton(new DuplicateButton(this));
    this.addActionButton(new DeleteButton(this));

    const capabilities = new Map();
    capabilities.set('duplicate', {
      enabled: true,
      fn: this.duplicate,
    });
    capabilities.set('split', {
      enabled: true,
      fn: this.split.bind(this),
    });

    this.block = this.blockDef.render(
      blockElement,
      this.prefix + '-value',
      initialState,
      undefined,
      capabilities,
    );

    if (this.collapsed) {
      this.collapse();
    }

    if (animate) {
      dom.hide();
      setTimeout(() => {
        dom.slideDown();
      }, 10);
    }
  }

  addActionButton(button) {
    button.render(this.actionsContainerElement);
  }

  moveUp() {
    this.sequence.moveBlockUp(this.index);
  }

  moveDown() {
    this.sequence.moveBlockDown(this.index);
  }

  duplicate(opts) {
    this.sequence.duplicateBlock(this.index, opts);
  }

  delete(opts) {
    this.sequence.deleteBlock(this.index, opts);
  }

  markDeleted({ animate = false }) {
    this.deletedInput.val('1');
    if (animate) {
      $(this.element).slideUp().dequeue().fadeOut().attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }

    // Inform the comment app that the content path of this block is no longer valid
    // This will hide any comments that were previously on the block
    const contentPath = this.getContentPath();
    if (contentPath && window.comments.commentApp) {
      window.comments.commentApp.invalidateContentPath(contentPath);
    }
  }

  getContentPath() {
    return window.comments?.getContentPath(this.element);
  }

  enableDuplication() {
    this.emit('enableDuplication');
    if (this.block && this.block.setCapabilityOptions) {
      this.block.setCapabilityOptions('duplicate', { enabled: true });
    }
  }

  disableDuplication() {
    this.emit('disableDuplication');
    if (this.block && this.block.setCapabilityOptions) {
      this.block.setCapabilityOptions('duplicate', { enabled: false });
    }
  }

  enableSplit() {
    if (this.block && this.block.setCapabilityOptions) {
      this.block.setCapabilityOptions('split', { enabled: true });
    }
  }

  disableSplit() {
    if (this.block && this.block.setCapabilityOptions) {
      this.block.setCapabilityOptions('split', { enabled: false });
    }
  }

  enableMoveUp() {
    this.emit('enableMoveUp');
  }

  disableMoveUp() {
    this.emit('disableMoveUp');
  }

  enableMoveDown() {
    this.emit('enableMoveDown');
  }

  disableMoveDown() {
    this.emit('disableMoveDown');
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

  getTextLabel(opts) {
    if (this.block.getTextLabel) {
      return this.block.getTextLabel(opts);
    }
    return null;
  }

  collapse() {
    this.contentElement.hide().attr('aria-hidden', 'true');
    const label = this.getTextLabel({ maxLength: 50 });
    this.titleElement.text(label || '');
    this.collapsed = true;
    this.contentElement
      .get(0)
      .dispatchEvent(
        new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
      );
  }

  expand() {
    this.contentElement.show().attr('aria-hidden', 'false');
    this.titleElement.text('');
    this.collapsed = false;
    this.contentElement
      .get(0)
      .dispatchEvent(
        new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
      );
  }

  toggleCollapsedState() {
    if (this.collapsed) {
      this.expand();
    } else {
      this.collapse();
    }
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

  delete({ animate = false }) {
    if (animate) {
      $(this.element).slideUp().attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }
  }
}

export class BaseSequenceBlock {
  /* eslint-disable @typescript-eslint/no-unused-vars */
  _createChild(
    blockDef,
    placeholder,
    prefix,
    index,
    id,
    initialState,
    sequence,
    opts,
  ) {
    throw new Error('not implemented');
  }

  _createInsertionControl(placeholder, opts) {
    throw new Error('not implemented');
  }

  _getChildDataForInsertion(opts) {
    throw new Error('not implemented');
  }
  /* eslint-enable @typescript-eslint/no-unused-vars */

  clear() {
    this.countInput.val(0);
    this.sequenceContainer.empty();
    this.children = [];
    this.blockCounter = 0;

    // Create initial insertion control
    const placeholder = document.createElement('div');
    this.sequenceContainer.append(placeholder);
    this.inserters = [
      this._createInsertionControl(placeholder, {
        index: 0,
        onRequestInsert: (newIndex, opts) => {
          this._onRequestInsert(newIndex, opts);
        },
        strings: this.blockDef.meta.strings,
      }),
    ];

    this.blockCountChanged();
  }

  _onRequestInsert(index, opts) {
    /* handler for an 'insert new block' action */
    const [blockDef, initialState, id] = this._getChildDataForInsertion(opts);
    const newChild = this._insert(blockDef, initialState, id || null, index, {
      animate: true,
    });
    // focus the newly added field if we can do so without obtrusive UI behaviour
    newChild.focus({ soft: true });
  }

  blockCountChanged() {
    /* Called whenever the block count has changed; subclasses can override this to apply
    checks on max block count and disable insert / duplicate controls accordingly */
  }

  _insert(childBlockDef, initialState, id, index, opts) {
    const prefix = this.prefix + '-' + this.blockCounter;
    const animate = opts && opts.animate;
    const collapsed = opts && opts.collapsed;
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

    const child = this._createChild(
      childBlockDef,
      blockPlaceholder,
      prefix,
      index,
      id,
      initialState,
      this,
      {
        animate,
        collapsed,
        strings: this.blockDef.meta.strings,
      },
    );
    this.children.splice(index, 0, child);

    const inserter = this._createInsertionControl(inserterPlaceholder, {
      index: index + 1,
      onRequestInsert: (newIndex, inserterOpts) => {
        this._onRequestInsert(newIndex, inserterOpts);
      },
      strings: this.blockDef.meta.strings,
      animate,
    });
    this.inserters.splice(index + 1, 0, inserter);

    this.countInput.val(this.blockCounter);

    const isFirstChild = index === 0;
    const isLastChild = index === this.children.length - 1;
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

    this.blockCountChanged();

    return child;
  }

  deleteBlock(index, opts) {
    const animate = opts && opts.animate;
    this.children[index].markDeleted({ animate });
    this.inserters[index].delete({ animate });
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

    this.blockCountChanged();
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

  moveBlockUp(index) {
    this.moveBlock(index, index - 1);
  }

  moveBlockDown(index) {
    this.moveBlock(index, index + 1);
  }

  setState(values) {
    this.clear();
    values.forEach((val, i) => {
      this.insert(val, i);
    });
  }

  getState() {
    return this.children.map((child) => child.getState());
  }

  getValue() {
    return this.children.map((child) => child.getValue());
  }

  getTextLabel(opts) {
    /* Use as many child text labels as we can fit into maxLength */
    const maxLength = opts && opts.maxLength;
    let result = '';

    for (const child of this.children) {
      const childLabel = child.getTextLabel({ maxLength });
      if (childLabel) {
        if (!result) {
          // always use the first child, truncated as necessary
          result = childLabel;
        } else {
          const newResult = result + ', ' + childLabel;
          if (maxLength && newResult.length > maxLength - 1) {
            // too long, so don't add this; return the current list with an ellipsis instead
            if (!result.endsWith('…')) result += '…';
            return result;
          }
          result = newResult;
        }
      }
    }
    return result;
  }

  focus(opts) {
    if (this.children.length) {
      this.children[0].focus(opts);
    }
  }
}
