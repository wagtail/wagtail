/* eslint-disable no-underscore-dangle */

import { v4 as uuidv4 } from 'uuid';

import {
  BaseSequenceBlock,
  BaseSequenceChild,
  BaseInsertionControl,
} from './BaseSequenceBlock';
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
    const animate = opts.animate;

    const dom = $(`
      <div>
        <button data-streamblock-menu-open type="button" title="${h(
          opts.strings.ADD,
        )}"
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
    this.canAddBlock = true;
    this.disabledBlockTypes = new Set();
    this.close({ animate: false });
    if (animate) {
      dom.hide().slideDown();
    }
  }

  renderMenu() {
    if (this.hasRenderedMenu) return;
    this.hasRenderedMenu = true;

    this.groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      if (group) {
        const heading = $('<h4 class="c-sf-add-panel__group-title"></h4>').text(
          group,
        );
        this.innerContainer.append(heading);
      }
      const grid = $('<div class="c-sf-add-panel__grid"></div>');
      this.innerContainer.append(grid);
      blockDefs.forEach((blockDef) => {
        const button = $(`
          <button type="button" class="c-sf-button action-add-block-${h(
            blockDef.name,
          )}">
            <svg class="icon icon-${h(
              blockDef.meta.icon,
            )} c-sf-button__icon" aria-hidden="true">
              <use href="#icon-${h(blockDef.meta.icon)}"></use>
            </svg>
            ${h(blockDef.meta.label)}
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

    // Disable buttons for any disabled block types
    this.disabledBlockTypes.forEach((blockType) => {
      $(`button.action-add-block-${h(blockType)}`, this.innerContainer).attr(
        'disabled',
        'true',
      );
    });
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

    // Close menu if its open and we no longer can add blocks
    if (!canAddBlock && this.isOpen) {
      this.close({ animate: true });
    }

    // Disable/enable individual block type buttons
    $('button', this.innerContainer).removeAttr('disabled');
    disabledBlockTypes.forEach((blockType) => {
      $(`button.action-add-block-${h(blockType)}`, this.innerContainer).attr(
        'disabled',
        'true',
      );
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
    if (!this.canAddBlock) {
      return;
    }

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

export class StreamBlock extends BaseSequenceBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${h(this.blockDef.meta.classname || '')}">
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

  /*
   * Called whenever a block is added or removed
   *
   * Updates the state of add / duplicate block buttons to prevent too many blocks being inserted.
   */
  blockCountChanged() {
    super.blockCountChanged();
    this.canAddBlock = true;

    if (
      typeof this.blockDef.meta.maxNum === 'number' &&
      this.children.length >= this.blockDef.meta.maxNum
    ) {
      this.canAddBlock = false;
    }

    // If we can add blocks, check if there are any block types that have count limits
    this.disabledBlockTypes = new Set();
    if (this.canAddBlock) {
      for (const blockType in this.blockDef.meta.blockCounts) {
        if (this.blockDef.meta.blockCounts.hasOwnProperty(blockType)) {
          const counts = this.blockDef.meta.blockCounts[blockType];

          if (typeof counts.max_num === 'number') {
            const currentBlockCount = this.children.filter(
              (child) => child.type === blockType,
            ).length;

            if (currentBlockCount >= counts.max_num) {
              this.disabledBlockTypes.add(blockType);
            }
          }
        }
      }
    }

    for (let i = 0; i < this.children.length; i++) {
      const canDuplicate =
        this.canAddBlock && !this.disabledBlockTypes.has(this.children[i].type);

      if (canDuplicate) {
        this.children[i].enableDuplication();
        this.children[i].enableSplit();
      } else {
        this.children[i].disableDuplication();
        this.children[i].disableSplit();
      }
    }
    for (let i = 0; i < this.inserters.length; i++) {
      this.inserters[i].setNewBlockRestrictions(
        this.canAddBlock,
        this.disabledBlockTypes,
      );
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
    const childState = child.getState();
    const animate = opts && opts.animate;
    childState.id = null;
    this.insert(childState, index + 1, { animate, collapsed: child.collapsed });
    // focus the newly added field if we can do so without obtrusive UI behaviour
    this.children[index + 1].focus({ soft: true });
  }

  splitBlock(index, valueBefore, valueAfter, shouldMoveCommentFn, opts) {
    const child = this.children[index];
    const animate = opts && opts.animate;
    const initialState = child.getState();
    const newChild = this.insert(
      { type: initialState.type, id: uuidv4(), value: valueAfter },
      index + 1,
      { animate, collapsed: child.collapsed },
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
    // focus the newly added field if we can do so without obtrusive UI behaviour
    this.children[index + 1].focus({ soft: true });
  }

  setState(values) {
    super.setState(values);
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
    container
      .querySelectorAll(':scope > .help-block.help-critical')
      .forEach((element) => element.remove());

    if (error.nonBlockErrors.length > 0) {
      // Add a help block for each error raised
      error.nonBlockErrors.forEach((nonBlockError) => {
        const errorElement = document.createElement('p');
        errorElement.classList.add('help-block');
        errorElement.classList.add('help-critical');
        errorElement.innerHTML = h(nonBlockError.messages[0]);
        container.insertBefore(errorElement, container.childNodes[0]);
      });
    }

    // Block errors

    for (const blockIndex in error.blockErrors) {
      if (error.blockErrors.hasOwnProperty(blockIndex)) {
        this.children[blockIndex].setError(error.blockErrors[blockIndex]);
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
