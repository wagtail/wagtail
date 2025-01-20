/* eslint-disable no-underscore-dangle */

/* global $ */

import EventEmitter from 'events';
import { v4 as uuidv4 } from 'uuid';
import Sortable from 'sortablejs';
import { escapeHtml as h } from '../../../utils/text';
import {
  initCollapsiblePanel,
  toggleCollapsiblePanel,
} from '../../../includes/panels';
import { range } from '../../../utils/range';

class ActionButton {
  constructor(sequenceChild) {
    this.sequenceChild = sequenceChild;
  }

  render(container) {
    const label =
      this.sequenceChild.strings[this.labelIdentifier] || this.labelIdentifier;

    this.dom = $(`
      <button type="button" class="button button--icon text-replace white" data-streamfield-action="${this.labelIdentifier}" title="${h(label)}">
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

class DragButton extends ActionButton {
  enableEvent = 'enableDrag';
  disableEvent = 'disableDrag';
  initiallyDisabled = false;
  icon = 'grip';
  labelIdentifier = 'DRAG';
}

class DuplicateButton extends ActionButton {
  enableEvent = 'enableDuplication';
  disableEvent = 'disableDuplication';
  icon = 'copy';
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
    super();
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;
    this.sequence = sequence;

    const animate = opts && opts.animate;
    const focus = opts && opts.focus;
    const collapsed = opts && opts.collapsed;
    this.strings = (opts && opts.strings) || {};

    const panelId = `block-${id}-section`;
    const headingId = `block-${id}-heading`;
    const contentId = `block-${id}-content`;
    const blockTypeIcon = h(this.blockDef.meta.icon);
    const blockTypeLabel = h(this.blockDef.meta.label);

    const dom = $(`
      <div data-streamfield-child ${
        this.id
          ? `data-contentpath="${h(this.id)}"`
          : 'data-contentpath-disabled'
      }>
        <input type="hidden" name="${this.prefix}-deleted" value="">
        <input type="hidden" name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${h(
          this.type || '',
        )}">
        <input type="hidden" name="${this.prefix}-id" value="${h(
          this.id || '',
        )}">
        <section class="w-panel w-panel--nested" id="${panelId}" aria-labelledby="${headingId}" data-panel>
          <div class="w-panel__header">
            <a class="w-panel__anchor w-panel__anchor--prefix" href="#${panelId}" aria-labelledby="${headingId}" data-panel-anchor>
              <svg class="icon icon-link w-panel__icon" aria-hidden="true">
                <use href="#icon-link"></use>
              </svg>
            </a>
            <button class="w-panel__toggle" type="button" aria-label="${'Toggle section'}" aria-describedby="${headingId}" data-panel-toggle aria-controls="${contentId}" aria-expanded="true">
              <svg class="icon icon-${blockTypeIcon} w-panel__icon" aria-hidden="true">
                <use href="#icon-${blockTypeIcon}"></use>
              </svg>
            </button>
            <h2 class="w-panel__heading w-panel__heading--label" aria-level="3" id="${headingId}" data-panel-heading>
              <span data-panel-heading-text class="c-sf-block__title"></span>
              <span class="c-sf-block__type">${blockTypeLabel}</span>
              ${
                blockDef.meta.required
                  ? '<span class="w-required-mark" data-panel-required>*</span>'
                  : ''
              }
            </h2>
            <a class="w-panel__anchor w-panel__anchor--suffix" href="#${panelId}" aria-labelledby="${headingId}">
              <svg class="icon icon-link w-panel__icon" aria-hidden="true">
                <use href="#icon-link"></use>
              </svg>
            </a>
            <div class="w-panel__divider"></div>
            <div class="w-panel__controls" data-panel-controls></div>
          </div>
          <div id="${contentId}" class="w-panel__content">
            <div data-streamfield-block></div>
          </div>
        </section>
      </div>
    `);

    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);
    const blockElement = dom.find('[data-streamfield-block]').get(0);
    this.actionsContainerElement = dom.find('[data-panel-controls]').get(0);
    this.titleElement = dom.find('[data-panel-heading-text]');
    this.toggleElement = this.element.querySelector('[data-panel-toggle]');
    this.deletedInput = dom.find(`input[name="${this.prefix}-deleted"]`);
    this.indexInput = dom.find(`input[name="${this.prefix}-order"]`);

    this.addActionButton(new MoveUpButton(this));
    this.addActionButton(new MoveDownButton(this));
    this.addActionButton(new DragButton(this));
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
    capabilities.set('addSibling', {
      enabled: true,
      fn: this.addSibling.bind(this),
      blockGroups: this.sequence.getBlockGroups(),
      getBlockCount: this.sequence.getBlockCount.bind(this.sequence),
      getBlockMax: this.sequence.getBlockMax.bind(this.sequence),
    });

    this.block = this.blockDef.render(
      blockElement,
      this.prefix + '-value',
      initialState,
      undefined,
      capabilities,
    );

    initCollapsiblePanel(this.element.querySelector('[data-panel-toggle]'));

    if (collapsed) {
      this.collapse();
    }

    this.toggleElement.addEventListener('wagtail:panel-toggle', () => {
      const label = this.getTextLabel({ maxLength: 50 });
      this.titleElement.text(label || '');
    });

    // Set in initialisation regardless of block state for screen reader users.
    const textLabel = this.getTextLabel({ maxLength: 50 });
    this.titleElement.text(textLabel || '');

    if (animate) {
      dom.hide();
      setTimeout(() => {
        dom.slideDown();
        if (focus) {
          // focus this field if we can do so without obtrusive UI behaviour
          this.block.focus({ soft: true });
        }
      }, 10);
    } else if (focus) {
      // focus this field if we can do so without obtrusive UI behaviour
      this.block.focus({ soft: true });
    }
  }

  addActionButton(button) {
    button.render(this.actionsContainerElement);
  }

  addSibling(opts) {
    this.sequence._onRequestInsert(this.index + 1, opts);
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

    // If there is an error, the panel should be expanded always so the error is not obscured
    if (error) {
      toggleCollapsiblePanel(this.toggleElement, true);
    }
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
    toggleCollapsiblePanel(this.toggleElement, false);
  }

  getDuplicatedState() {
    return {
      id: uuidv4(),
      value:
        this.block.getDuplicatedState === undefined
          ? this.block.getState()
          : this.block.getDuplicatedState(),
    };
  }
}

/**
 * Base class for controls that appear between blocks in a sequence, to allow inserting new
 * blocks at that point. Subclasses should render an HTML structure with a single root element
 * (replacing the placeholder passed to the constructor) and set it as this.element.
 * When the user requests to insert a block, we call onRequestInsert passing the index number
 * and a dict of control-specific options.
 */
export class BaseInsertionControl {
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

  getBlockGroups() {
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
    this._insert(blockDef, initialState, id || null, index, {
      animate: true,
      focus: true,
    });
  }

  /**
   * Called whenever the block count has changed; subclasses can override this to apply
   * checks on max block count and disable insert / duplicate controls accordingly.
   */
  blockCountChanged() {}

  _insert(childBlockDef, initialState, id, index, opts) {
    const prefix = this.prefix + '-' + this.blockCounter;
    const animate = opts && opts.animate;
    const focus = opts && opts.focus;
    const collapsed = opts && opts.collapsed;
    this.blockCounter += 1;

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
    range(index, this.children.length).forEach((i) => {
      this.children[i].setIndex(i + 1);
    });
    range(index + 1, this.inserters.length).forEach((i) => {
      this.inserters[i].setIndex(i + 1);
    });

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
        focus,
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
    range(index, this.children.length).forEach((i) => {
      this.children[i].setIndex(i);
    });
    range(index, this.inserters.length).forEach((i) => {
      this.inserters[i].setIndex(i);
    });

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

  initDragNDrop() {
    this.sortable = Sortable.create(this.sequenceContainer.get(0), {
      handle: '[data-streamfield-action="DRAG"]',
      animation: 200,
      // Only drag blocks, not insertion controls.
      draggable: '[data-streamfield-child]',
      onEnd: (e) => {
        // Only consider StreamField blocks, not the insertion controls.
        const { oldDraggableIndex, newDraggableIndex } = e;
        if (oldDraggableIndex !== newDraggableIndex) {
          this.moveBlock(oldDraggableIndex, newDraggableIndex);
        }
      },
      setData: (dataTransfer) => {
        dataTransfer.setData('application/vnd.wagtail.type', 'sf-block');
      },
    });
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
      range(oldIndex, newIndex + 1).forEach((i) => {
        this.inserters[i].setIndex(i);
        this.children[i].setIndex(i);
      });
    } else {
      range(newIndex, oldIndex + 1).forEach((i) => {
        this.inserters[i].setIndex(i);
        this.children[i].setIndex(i);
      });
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

  getDuplicatedState() {
    return this.children.map((child) => child.getDuplicatedState());
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
