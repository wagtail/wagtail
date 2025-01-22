/* global $ */

import { v4 as uuidv4 } from 'uuid';

import {
  BaseSequenceBlock,
  BaseSequenceChild,
  BaseInsertionControl,
} from './BaseSequenceBlock';
import { escapeHtml as h } from '../../../utils/text';
import { gettext } from '../../../utils/gettext';
import {
  addErrorMessages,
  removeErrorMessages,
} from '../../../includes/streamFieldErrors';

/**
 * Wrapper for an item inside a ListBlock
 */
class ListChild extends BaseSequenceChild {
  getState() {
    return {
      id: this.id || null,
      value: this.block.getState(),
    };
  }

  getValue() {
    return this.block.getValue();
  }

  setState({ value, id }) {
    this.block.setState(value);
    this.id = id === undefined ? null : id;
  }

  setValue(value) {
    this.block.setState(value);
  }

  split(valueBefore, valueAfter, shouldMoveCommentFn, opts) {
    this.sequence.splitBlock(
      this.index,
      valueBefore,
      valueAfter,
      shouldMoveCommentFn,
      opts,
    );
  }
}

/**
 * Represents a position in the DOM where a new list item can be inserted.
 *
 * @description
 * This renders a + button. Later, these could also be used to represent drop zones for drag+drop reordering.
 */
class InsertPosition extends BaseInsertionControl {
  constructor(placeholder, opts) {
    super(placeholder, opts);
    this.onRequestInsert = opts && opts.onRequestInsert;
    const animate = opts && opts.animate;
    const title = h(opts.strings.ADD);
    const button = $(`
      <button type="button" title="${title}" data-streamfield-list-add class="c-sf-add-button">
        <svg class="icon icon-plus" aria-hidden="true"><use href="#icon-plus"></use></svg>
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
    super();
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(
          prefix,
        )}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    if (this.blockDef.meta.helpText) {
      // help text is left unescaped as per Django conventions
      $(`
        <div class="c-sf-help">
          <div class="help">
            ${this.blockDef.meta.helpText}
          </div>
        </div>
      `).insertBefore(dom);
    }

    this.children = [];
    this.inserters = [];
    this.blockCounter = 0;
    this.countInput = dom.find('[data-streamfield-list-count]');
    this.sequenceContainer = dom.find('[data-streamfield-list-container]');
    this.container = dom;
    this.setState(initialState || []);
    if (this.blockDef.meta.collapsed) {
      this.children.forEach((block) => {
        block.collapse();
      });
    }

    if (initialError) {
      this.setError(initialError);
    }

    this.initDragNDrop();
  }

  /**
   * State for a ListBlock is a list of {id, value} objects, but
   * ListBlock.insert accepts the value as first argument; id is passed in the options dict instead.
   */
  setState(blocks) {
    this.clear();
    blocks.forEach(({ value, id }, i) => {
      const validId = id === undefined ? uuidv4() : id;
      this.insert(value, i, { id: id || validId });
    });
  }

  /**
   * Called when an 'insert new block' action is triggered: given a dict of data from the insertion control,
   * return the block definition and initial state to be used for the new block.
   * For a ListBlock, no data is passed from the insertion control, as there is a single fixed child block definition.
   */
  _getChildDataForInsertion() {
    const blockDef = this.blockDef.childBlockDef;
    const initialState = this.blockDef.initialChildState;
    return [blockDef, initialState, uuidv4()];
  }

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
    return new ListChild(
      blockDef,
      placeholder,
      prefix,
      index,
      id,
      initialState,
      sequence,
      opts,
    );
  }

  _createInsertionControl(placeholder, opts) {
    return new InsertPosition(placeholder, opts);
  }

  /**
   * Called whenever a block is added or removed
   *
   * Updates the state of add / duplicate block buttons to prevent too many blocks being inserted.
   */
  blockCountChanged() {
    super.blockCountChanged();

    const errorMessages = [];
    const maxNum = this.blockDef.meta.maxNum;

    if (typeof maxNum === 'number') {
      if (this.children.length > maxNum) {
        const message = gettext(
          'The maximum number of items is %(max_num)d',
        ).replace('%(max_num)d', `${maxNum}`);
        errorMessages.push(message);
      }
    }

    const minNum = this.blockDef.meta.minNum;

    if (typeof minNum === 'number') {
      if (this.children.length < minNum) {
        const message = gettext(
          'The minimum number of items is %(min_num)d',
        ).replace('%(min_num)d', `${minNum}`);
        errorMessages.push(message);
      }
    }

    if (errorMessages.length) {
      this.setError({ messages: errorMessages });
    } else {
      this.setError({});
    }
  }

  insert(value, index, opts) {
    // eslint-disable-next-line no-underscore-dangle
    return this._insert(
      this.blockDef.childBlockDef,
      value,
      opts?.id,
      index,
      opts,
    );
  }

  duplicateBlock(index, opts) {
    const child = this.children[index];
    const { id: newId, value: childValue } = child.getDuplicatedState();
    const animate = opts && opts.animate;
    this.insert(childValue, index + 1, {
      animate,
      focus: true,
      collapsed: child.collapsed,
      id: newId,
    });
  }

  splitBlock(index, valueBefore, valueAfter, shouldMoveCommentFn, opts) {
    const child = this.children[index];
    const animate = opts && opts.animate;
    child.setValue(valueBefore);
    const newChild = this.insert(valueAfter, index + 1, {
      animate,
      focus: true,
      collapsed: child.collapsed,
    });
    const oldContentPath = child.getContentPath();
    const newContentPath = newChild.getContentPath();
    const commentApp = window.comments?.commentApp;
    if (oldContentPath && newContentPath && commentApp) {
      // Move comments from the old contentpath to the new
      // We allow use of a custom function to determine whether to move each comment
      // so it can be done based on intra-field position
      const selector =
        commentApp.utils.selectCommentsForContentPathFactory(oldContentPath);
      const comments = selector(commentApp.store.getState());
      comments.forEach((comment) => {
        if (shouldMoveCommentFn(comment)) {
          commentApp.updateContentPath(comment.localId, newContentPath);
        }
      });
    }
  }

  setError(error) {
    if (!error) return;

    // Non block errors
    const container = this.container[0];
    removeErrorMessages(container);

    if (error.messages) {
      addErrorMessages(container, error.messages);
    }

    if (error.blockErrors) {
      // error.blockErrors = a dict of errors, keyed by block index
      Object.entries(error.blockErrors).forEach(([index, blockError]) => {
        this.children[index].setError(blockError);
      });
    }
  }

  getBlockGroups() {
    const group = ['', [this.blockDef.childBlockDef]];
    return [group];
  }

  getBlockCount() {
    return this.children.length;
  }

  getBlockMax() {
    return this.blockDef.meta.maxNum || 0;
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
