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
import { range } from '../../../utils/range';
import ComboBox, {
  comboBoxLabel,
  comboBoxNoResults,
  comboBoxTriggerLabel,
} from '../../ComboBox/ComboBox';
import { hideTooltipOnEsc } from '../../../includes/initTooltips';
import {
  addErrorMessages,
  removeErrorMessages,
} from '../../../includes/streamFieldErrors';

/* global $ */

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

  getDuplicatedState() {
    return {
      ...super.getDuplicatedState(),
      type: this.type,
    };
  }

  setState({ type, value, id }) {
    this.type = type;
    this.block.setState(value);
    this.id = id;
  }

  getValue() {
    return {
      type: this.type,
      value: this.block.getValue(),
      id: this.id,
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
    this.combobox = document.createElement('div');
    this.canAddBlock = true;
    this.disabledBlockTypes = new Set();

    this.tooltip = tippy(this.addButton.get(0), {
      content: this.combobox,
      trigger: 'click',
      interactive: true,
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

  renderMenu() {
    const items = this.groupedChildBlockDefs.map(([group, blockDefs]) => {
      const groupItems = blockDefs
        // Allow adding all blockDefs even when disabled, so validation only impedes when saving.
        // Keeping the previous filtering here for future reference.
        // .filter((blockDef) => !this.disabledBlockTypes.has(blockDef.name))
        .map((blockDef) => ({
          type: blockDef.name,
          label: blockDef.meta.label,
          icon: blockDef.meta.icon,
        }));

      return {
        label: group || '',
        type: group || '',
        items: groupItems,
      };
    });

    ReactDOM.render(
      <ComboBox
        label={comboBoxLabel}
        placeholder={comboBoxLabel}
        items={items}
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

  setNewBlockRestrictions(canAddBlock, disabledBlockTypes) {
    this.canAddBlock = canAddBlock;
    this.disabledBlockTypes = disabledBlockTypes;
    // Disable/enable menu open button
    if (this.canAddBlock) {
      this.addButton.removeAttr('disabled');
    } else {
      this.addButton.attr('disabled', 'true');
    }
  }

  open() {
    if (!this.canAddBlock) {
      return;
    }
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
    this.container = dom;

    if (initialError) {
      this.setError(initialError);
    }
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

  /*
   * Called whenever a block is added or removed
   *
   * Updates the state of add / duplicate block buttons to prevent too many blocks being inserted.
   */
  blockCountChanged() {
    super.blockCountChanged();
    this.canAddBlock = true;
    this.childBlockCounts.clear();

    if (
      typeof this.blockDef.meta.maxNum === 'number' &&
      this.children.length >= this.blockDef.meta.maxNum
    ) {
      this.canAddBlock = false;
    }

    // Check if there are any block types that have count limits
    this.disabledBlockTypes = new Set();
    for (const blockType in this.blockDef.meta.blockCounts) {
      if (hasOwn(this.blockDef.meta.blockCounts, blockType)) {
        const maxNum = this.getBlockMax(blockType);

        if (typeof maxNum === 'number') {
          const currentBlockCount = this.getBlockCount(blockType);

          if (currentBlockCount >= maxNum) {
            this.disabledBlockTypes.add(blockType);
          }
        }
      }
    }

    range(0, this.inserters.length).forEach((i) => {
      this.inserters[i].setNewBlockRestrictions(
        this.canAddBlock,
        this.disabledBlockTypes,
      );
    });
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

  _getChildDataForInsertion({ type }) {
    /* Called when an 'insert new block' action is triggered: given a dict of data from the insertion control,
    return the block definition and initial state to be used for the new block.
    For a StreamBlock, the dict of data consists of 'type' (the chosen block type name, as a string).
    */
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
      id: initialState.id,
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
