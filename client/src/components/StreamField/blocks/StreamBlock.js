/* eslint-disable no-underscore-dangle */
import React from 'react';
import ReactDOM from 'react-dom';
import { v4 as uuidv4 } from 'uuid';
import tippy from 'tippy.js';

import {
  BaseSequenceBlock,
  BaseSequenceChild,
  BaseInsertionControl,
} from './BaseSequenceBlock';
import { escapeHtml as h } from '../../../utils/text';
import { hasOwn } from '../../../utils/hasOwn';
import { gettext } from '../../../utils/gettext';
import ComboBox, {
  comboBoxLabel,
  comboBoxNoResults,
  comboBoxTriggerLabel,
} from '../../ComboBox/ComboBox';
import { hideTooltipOnEsc } from '../../../controllers/TooltipController';
import {
  addErrorMessages,
  removeErrorMessages,
} from '../../../includes/streamFieldErrors';

/* global $ */

class StreamChild extends BaseSequenceChild {
  /**
   * wrapper for a block inside a StreamBlock, handling StreamBlock-specific metadata
   * such as id
   * @returns {Object} - The state of the child block
   */
  getState() {
    return {
      type: this.type,
      value: this.block.getState(),
      id: this.id || null,
    };
  }

  getDuplicatedState() {
    return {
      ...super.getDuplicatedState(),
      type: this.type,
    };
  }

  setState({ type, value, id }) {
    this.type = type;
    this.block.setState(value);
    this.id = id === undefined ? null : id;
  }

  getValue() {
    return {
      type: this.type,
      value: this.block.getValue(),
      id: this.id || null,
    };
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

class StreamBlockMenu extends BaseInsertionControl {
  constructor(placeholder, opts) {
    super(placeholder, opts);
    this.groupedChildBlockDefs = opts.groupedChildBlockDefs;

    const dom = $(`
      <div>
        <button type="button" title="${comboBoxTriggerLabel}" class="c-sf-add-button">
          <svg class="icon icon-plus" aria-hidden="true"><use href="#icon-plus"></use></svg>
        </button>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);
    this.addButton = dom.find('button');

    const blockItems = this.blockItems;
    if (blockItems.length === 1 && blockItems[0].items.length === 1) {
      // Only one child type can be added, bypass the combobox
      this.addButton.click(() => {
        if (this.onRequestInsert) {
          this.onRequestInsert(this.index, blockItems[0].items[0]);
        }
      });
      return;
    }

    this.combobox = document.createElement('div');

    this.tooltip = tippy(this.addButton.get(0), {
      content: this.combobox,
      trigger: 'click',
      interactive: true,
      maxWidth: 'none',
      theme: 'dropdown',
      arrow: false,
      placement: 'bottom',
      plugins: [hideTooltipOnEsc],
      onShow: this.renderMenu.bind(this),
      onHidden: () => {
        ReactDOM.render(null, this.combobox);
      },
    });
  }

  get blockItems() {
    return this.groupedChildBlockDefs.map(([group, blockDefs]) => {
      const groupItems = blockDefs.map((blockDef) => ({
        type: blockDef.name,
        label: blockDef.meta.label,
        description: blockDef.meta.description,
        icon: blockDef.meta.icon,
        blockDefId: blockDef.meta.blockDefId,
        isPreviewable: blockDef.meta.isPreviewable,
      }));

      return {
        label: group || '',
        type: group || '',
        items: groupItems,
      };
    });
  }

  renderMenu() {
    const blockItems = this.blockItems;
    ReactDOM.render(
      <ComboBox
        label={comboBoxLabel}
        placeholder={comboBoxLabel}
        items={blockItems}
        getItemLabel={(type, item) => item.label}
        getItemDescription={(item) => item.label}
        getSearchFields={(item) => [item.label, item.type]}
        noResultsText={comboBoxNoResults}
        onSelect={this.onSelectBlock.bind(this)}
      />,
      this.combobox,
    );
  }

  onSelectBlock(change) {
    if (this.onRequestInsert) {
      this.onRequestInsert(this.index, { type: change.selectedItem.type });
    }
    this.close();
  }

  open() {
    this.addButton.attr('aria-expanded', 'true');
    this.tooltip.show();
  }

  close() {
    this.addButton.attr('aria-expanded', 'false');
    this.tooltip.hide();
  }
}

export class StreamBlock extends BaseSequenceBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    super();
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(
          prefix,
        )}-count" data-streamfield-stream-count value="0">
        <div data-streamfield-stream-container></div>
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
    this.container = dom;

    // StreamChild objects for the current (non-deleted) child blocks
    this.children = [];

    // Cache for child block counting (not guaranteed to be fully populated)
    this.childBlockCounts = new Map();

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
    this.sequenceContainer = dom.find('[data-streamfield-stream-container]');
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

  getBlockGroups() {
    return this.blockDef.groupedChildBlockDefs;
  }

  getBlockCount(type) {
    // Get the block count for a particular type, or if none is provided, the total block count
    if (!type) {
      return this.children.length;
    }
    if (!this.childBlockCounts.has(type)) {
      this._updateBlockCount(type);
    }
    return this.childBlockCounts.get(type) || 0;
  }

  getBlockMax(type) {
    // Get the maximum number of blocks allowable for a particular type, or if none is provided, the total maximum
    if (!type) {
      return this.blockDef.meta.maxNum;
    }
    return this.blockDef.meta.blockCounts[type]?.max_num;
  }

  _updateBlockCount(type) {
    const currentBlockCount = this.children.filter(
      (child) => child.type === type,
    ).length;
    this.childBlockCounts.set(type, currentBlockCount);
  }

  /**
   * Called whenever a block is added or removed
   * Updates the state of add / duplicate block buttons to prevent too many blocks being inserted.
   */
  blockCountChanged() {
    super.blockCountChanged();
    this.childBlockCounts.clear();

    const errorMessages = [];

    const maxNum = this.blockDef.meta.maxNum;
    if (typeof maxNum === 'number' && this.children.length > maxNum) {
      const message = gettext(
        'The maximum number of items is %(max_num)d',
      ).replace('%(max_num)d', `${maxNum}`);
      errorMessages.push(message);
    }

    const minNum = this.blockDef.meta.minNum;
    if (typeof minNum === 'number' && this.children.length < minNum) {
      const message = gettext(
        'The minimum number of items is %(min_num)d',
      ).replace('%(min_num)d', `${minNum}`);
      errorMessages.push(message);
    }

    // Check if there are any block types that have count limits
    for (const [blockType, constraints] of Object.entries(
      this.blockDef.meta.blockCounts,
    )) {
      const blockMaxNum = constraints.max_num;
      if (typeof blockMaxNum === 'number') {
        const currentBlockCount = this.getBlockCount(blockType);

        if (currentBlockCount > blockMaxNum) {
          const childBlockDef = this.blockDef.childBlockDefsByName[blockType];
          const message = gettext(
            'The maximum number of items is %(max_num)d',
          ).replace('%(max_num)d', `${blockMaxNum}`);
          const messageWithPrefix = `${childBlockDef.meta.label}: ${message}`;
          errorMessages.push(messageWithPrefix);
        }
      }

      const blockMinNum = constraints.min_num;
      if (typeof blockMinNum === 'number') {
        const currentBlockCount = this.getBlockCount(blockType);

        if (currentBlockCount < blockMinNum) {
          const childBlockDef = this.blockDef.childBlockDefsByName[blockType];
          const message = gettext(
            'The minimum number of items is %(min_num)d',
          ).replace('%(min_num)d', `${blockMinNum}`);
          const messageWithPrefix = `${childBlockDef.meta.label}: ${message}`;
          errorMessages.push(messageWithPrefix);
        }
      }
    }

    if (errorMessages.length) {
      this.setError({ messages: errorMessages });
    } else {
      this.setError({});
    }
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
    return new StreamChild(
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
    // eslint-disable-next-line no-param-reassign
    opts.groupedChildBlockDefs = this.blockDef.groupedChildBlockDefs;
    return new StreamBlockMenu(placeholder, opts);
  }

  insert({ type, value, id }, index, opts) {
    const childBlockDef = this.blockDef.childBlockDefsByName[type];
    return this._insert(childBlockDef, value, id, index, opts);
  }

  /**
   * Called when an 'insert new block' action is triggered: given a dict of data from the insertion control.
   * For a StreamBlock, the dict of data consists of 'type' (the chosen block type name, as a string).
   *
   * @returns {Array} - The block definition, initial state, and id for the new block
   */
  _getChildDataForInsertion({ type }) {
    const blockDef = this.blockDef.childBlockDefsByName[type];
    const initialState = this.blockDef.initialChildStates[type];
    return [blockDef, initialState, uuidv4()];
  }

  duplicateBlock(index, opts) {
    const child = this.children[index];
    const childState = child.getDuplicatedState();
    const animate = opts && opts.animate;
    this.insert(childState, index + 1, {
      animate,
      focus: true,
      collapsed: child.collapsed,
    });
  }

  splitBlock(index, valueBefore, valueAfter, shouldMoveCommentFn, opts) {
    const child = this.children[index];
    const animate = opts && opts.animate;
    const initialState = child.getState();
    const newChild = this.insert(
      { type: initialState.type, id: uuidv4(), value: valueAfter },
      index + 1,
      { animate, focus: true, collapsed: child.collapsed },
    );
    child.setState({
      type: initialState.type,
      id: initialState.id || null,
      value: valueBefore,
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

  setState(values) {
    super.setState(values);
  }

  setError(error) {
    if (!error) return;

    // Non block errors (messages applying to the block as a whole)
    const container = this.container[0];
    removeErrorMessages(container);

    if (error.messages) {
      addErrorMessages(container, error.messages);
    }

    if (error.blockErrors) {
      // Block errors (to be propagated to child blocks)
      for (const blockIndex in error.blockErrors) {
        if (hasOwn(error.blockErrors, blockIndex)) {
          this.children[blockIndex].setError(error.blockErrors[blockIndex]);
        }
      }
    }
  }
}

export class StreamBlockDefinition {
  constructor(name, groupedChildBlockDefs, initialChildStates, meta) {
    this.name = name;
    this.groupedChildBlockDefs = groupedChildBlockDefs;
    this.initialChildStates = initialChildStates;
    this.childBlockDefsByName = {};
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    this.groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      blockDefs.forEach((blockDef) => {
        this.childBlockDefsByName[blockDef.name] = blockDef;
      });
    });
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new StreamBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}
