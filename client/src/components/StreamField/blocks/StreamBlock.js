import { BaseSequenceChild } from './BaseSequenceBlock';

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

class StreamBlockMenu {
  constructor(placeholder, groupedChildBlockDefs, opts) {
    this.index = opts && opts.index;
    this.onSelectBlockType = opts && opts.onSelectBlockType;
    this.isOpen = (opts && opts.isOpen) || false;

    const dom = $(`
      <div>
        <button data-streamblock-menu-open type="button" title="Add" class="c-sf-add-button c-sf-add-button--visible">
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
    const innerContainer = dom.find('[data-streamblock-menu-inner]');

    groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      if (group) {
        const heading = $('<h4 class="c-sf-add-panel__group-title"></h4>').text(group);
        innerContainer.append(heading);
      }
      const grid = $('<div class="c-sf-add-panel__grid"></div>');
      innerContainer.append(grid);
      blockDefs.forEach(blockDef => {
        const button = $(`
          <button type="button" class="c-sf-button action-add-block-${blockDef.name}">
            <span class="c-sf-button__icon">
              <i class="icon icon-${blockDef.meta.icon}"></i>
            </span>
            <span class="c-sf-button__label">${blockDef.meta.label}</span>
          </button>
        `);
        grid.append(button);
        button.click(() => {
          if (this.onSelectBlockType) {
            this.onSelectBlockType(blockDef.name, this.index);
          }
          this.close({ animate: true });
        });
      });
    });

    if (this.isOpen) {
      this.open({ animate: false });
    } else {
      this.close({ animate: false });
    }
  }

  setIndex(newIndex) {
    this.index = newIndex;
  }

  toggle() {
    if (this.isOpen) {
      this.close({ animate: true });
    } else {
      this.open({ animate: true });
    }
  }
  open(opts) {
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
  delete() {
    $(this.element).hide().attr('aria-hidden', 'true');
  }
}

export class StreamBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${this.blockDef.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-stream-count value="0">
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

    // StreamBlockMenu objects - there are one more of these than there are children.
    // The menu at index n will insert a block at index n
    this.menus = [];

    // Incrementing counter used to generate block prefixes, also reflected in the
    // 'count' hidden input. This count includes deleted items
    this.blockCounter = 0;
    this.countInput = dom.find('[data-streamfield-stream-count]');

    // Parent element of menu and block elements (potentially including deleted items,
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
    this.menus = [
      new StreamBlockMenu(
        placeholder, this.blockDef.groupedChildBlockDefs, {
          index: 0,
          isOpen: false,
          onSelectBlockType: (blockType, newIndex) => {
            this.insertFromMenu(blockType, newIndex);
          },
        }
      )
    ];
  }

  insert({ type, value, id }, index, opts) {
    const blockDef = this.blockDef.childBlockDefsByName[type];
    const prefix = this.prefix + '-' + this.blockCounter;
    const animate = opts && opts.animate;
    this.blockCounter++;

    /*
    a new menu and block will be inserted AFTER the menu with the given index;
    e.g if there are 3 blocks the children of streamContainer will be
    [menu 0, block 0, menu 1, block 1, menu 2, block 2, menu 3]
    and inserting a new block at index 1 will create a new block 1 and menu 2 after the
    current menu 1, and increment everything after that point
    */
    const existingMenuElement = this.menus[index].element;
    const blockPlaceholder = document.createElement('div');
    const menuPlaceholder = document.createElement('div');
    $(blockPlaceholder).insertAfter(existingMenuElement);
    $(menuPlaceholder).insertAfter(blockPlaceholder);

    /* shuffle up indexes of all blocks / menus above this index */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i + 1);
    }
    for (let i = index + 1; i < this.menus.length; i++) {
      this.menus[i].setIndex(i + 1);
    }

    const child = new StreamChild(blockDef, blockPlaceholder, prefix, index, id, value, {
      animate,
      onRequestDelete: (i) => { this.deleteBlock(i); }
    });
    this.children.splice(index, 0, child);

    const menu = new StreamBlockMenu(
      menuPlaceholder, this.blockDef.groupedChildBlockDefs, {
        index: index + 1,
        isOpen: false,
        onSelectBlockType: (blockType, newIndex) => {
          this.insertFromMenu(blockType, newIndex);
        },
      }
    );
    this.menus.splice(index + 1, 0, menu);

    this.countInput.val(this.blockCounter);
    return child;
  }

  insertFromMenu(blockType, index) {
    /* handle selecting an item from the 'add block' menu */
    const newBlock = this.insert({
      type: blockType,
      value: this.blockDef.initialChildStates[blockType],
    }, index, { animate: true });
    newBlock.focus();
  }

  deleteBlock(index) {
    this.children[index].markDeleted({ animate: true });
    this.menus[index].delete();
    this.children.splice(index, 1);
    this.menus.splice(index, 1);

    /* index numbers of children / menus above this index now need updating to match
    their array indexes */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i);
    }
    for (let i = index; i < this.menus.length; i++) {
      this.menus[i].setIndex(i);
    }
  }

  setState(values) {
    this.clear();
    values.forEach((val, i) => {
      this.insert(val, i);
    });
    if (values.length === 0) {
      /* for an empty list, begin with the menu open */
      this.menus[0].open({ animate: false });
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
