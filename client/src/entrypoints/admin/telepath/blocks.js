/* eslint-disable no-warning-comments */

/* global $ */

function initBlockWidget(id) {
  /*
  Initialises the top-level element of a BlockWidget
  (i.e. the form widget for a StreamField).
  Receives the ID of a DOM element with the attributes:
    data-block: JSON-encoded block definition to be passed to telepath.unpack
      to obtain a Javascript representation of the block
      (i.e. an instance of one of the Block classes below)
    data-value: JSON-encoded value for this block
  */

  const body = document.getElementById(id);

  // unpack the block definition and value
  const blockDefData = JSON.parse(body.dataset.block);
  const blockDef = window.telepath.unpack(blockDefData);
  const blockValue = JSON.parse(body.dataset.value);

  // replace the 'body' element with the populated HTML structure for the block
  blockDef.render(body, id, blockValue);
}
window.initBlockWidget = initBlockWidget;


class FieldBlock {
  constructor(blockDef, placeholder, prefix, initialState) {
    this.blockDef = blockDef;
    this.type = blockDef.name;

    const dom = $(`
      <div class="${this.blockDef.meta.classname || ''}">
        <div class="field-content">
          <div class="input">
            <div data-streamfield-widget></div>
            <span></span>
          </div>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    const widgetElement = dom.find('[data-streamfield-widget]').get(0);
    this.widget = this.blockDef.widget.render(widgetElement, prefix, prefix, initialState);
  }

  setState(state) {
    this.widget.setState(state);
  }

  getState() {
    return this.widget.getState();
  }

  getValue() {
    return this.widget.getValue();
  }

  focus() {
    this.widget.focus();
  }
}

class FieldBlockDefinition {
  constructor(name, widget, meta) {
    this.name = name;
    this.widget = widget;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState) {
    return new FieldBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);


class StructBlock {
  constructor(blockDef, placeholder, prefix, initialState) {
    const state = initialState || {};
    this.blockDef = blockDef;
    this.type = blockDef.name;

    const dom = $(`
      <div class="${this.blockDef.meta.classname || ''}">
      </div>
    `);
    $(placeholder).replaceWith(dom);

    this.childBlocks = {};
    this.blockDef.childBlockDefs.forEach(childBlockDef => {
      const childDom = $(`
        <div class="field">
          <label class="field__label">${childBlockDef.meta.label}</label>
          <div data-streamfield-block></div>
        </div>
      `);
      dom.append(childDom);
      const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
      const childBlock = childBlockDef.render(
        childBlockElement, prefix + '-' + childBlockDef.name, state[childBlockDef.name]
      );

      this.childBlocks[childBlockDef.name] = childBlock;
    });
  }

  setState(state) {
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in state) {
      this.childBlocks[name].setState(state[name]);
    }
  }

  getState() {
    const state = {};
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in this.childBlocks) {
      state[name] = this.childBlocks[name].getState();
    }
    return state;
  }

  getValue() {
    const value = {};
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in this.childBlocks) {
      value[name] = this.childBlocks[name].getValue();
    }
    return value;
  }

  focus() {
    if (this.blockDef.childBlockDefs.length) {
      const firstChildName = this.blockDef.childBlockDefs[0].name;
      this.childBlocks[firstChildName].focus();
    }
  }
}

class StructBlockDefinition {
  constructor(name, childBlockDefs, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState) {
    return new StructBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);


class ListBlock {
  constructor(blockDef, placeholder, prefix, initialState) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const dom = $(`
      <div class="c-sf-container ${this.blockDef.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
        <button type="button" title="Add" data-streamfield-list-add class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
      </div>
    `);
    $(placeholder).replaceWith(dom);

    this.childBlocks = [];
    this.countInput = dom.find('[data-streamfield-list-count]');
    this.listContainer = dom.find('[data-streamfield-list-container]');
    this.setState(initialState || []);
  }

  clear() {
    this.countInput.val(0);
    this.listContainer.empty();
    this.childBlocks = [];
  }

  append(value) {
    const index = this.childBlocks.length;
    const childPrefix = this.prefix + '-' + index;
    const childDom = $(`
      <div id="${childPrefix}-container" aria-hidden="false">
        <input type="hidden" id="${childPrefix}-deleted" name="${childPrefix}-deleted" value="">
        <input type="hidden" id="${childPrefix}-order" name="${childPrefix}-order" value="${index}">
        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${this.blockDef.childBlockDef.meta.icon}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type"></span>
                  <button type="button" id="${childPrefix}-moveup" class="c-sf-block__actions__single"
                      title="{% trans 'Move up' %}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" id="${childPrefix}-movedown" class="c-sf-block__actions__single"
                      title="{% trans 'Move down' %}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" id="${childPrefix}-delete" class="c-sf-block__actions__single"
                      title="{% trans 'Delete' %}">
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

    this.listContainer.append(childDom);
    const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
    const childBlock = this.blockDef.childBlockDef.render(childBlockElement, childPrefix + '-value', value);
    this.childBlocks.push(childBlock);
    this.countInput.val(this.childBlocks.length);
  }

  setState(values) {
    this.clear();
    values.forEach(val => {
      this.append(val);
    });
  }

  getState() {
    return this.childBlocks.map((block) => block.getState());
  }

  getValue() {
    return this.childBlocks.map((block) => block.getValue());
  }

  focus() {
    if (this.childBlocks.length) {
      this.childBlocks[0].focus();
    }
  }
}

class ListBlockDefinition {
  constructor(name, childBlockDef, initialChildState, meta) {
    this.name = name;
    this.childBlockDef = childBlockDef;
    this.initialChildState = initialChildState;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState) {
    return new ListBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);


class StreamChild {
  /*
  wrapper for a block inside a StreamBlock, handling StreamBlock-specific metadata
  such as id
  */
  constructor(blockDef, placeholder, prefix, index, id, state) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.id = id;

    const dom = $(`
      <div aria-hidden="false">
        <input type="hidden" name="${this.prefix}-deleted" value="">
        <input type="hidden" data-streamblock-index name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${this.type}">
        <input type="hidden" name="${this.prefix}-id" value="${this.id || ''}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${this.blockDef.meta.icon}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type">${this.blockDef.meta.label}</span>
                  <button type="button" class="c-sf-block__actions__single" title="{% trans 'Move up' %}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" class="c-sf-block__actions__single" title="{% trans 'Move down' %}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" class="c-sf-block__actions__single" title="{% trans 'Delete' %}">
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
    this.block = this.blockDef.render(blockElement, this.prefix + '-value', state);

    this.indexInput = dom.find('[data-streamblock-index]');
  }

  setIndex(newIndex) {
    this.indexInput.val(newIndex);
  }

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

  focus() {
    this.block.focus();
  }
}

class StreamBlockMenu {
  constructor(placeholder, groupedChildBlockDefs, opts) {
    this.index = opts && opts.index;
    this.onclick = opts && opts.onclick;
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
          if (this.onclick) {
            this.onclick(blockDef.name, this.index);
          }
          this.close(true);
        });
      });
    });

    if (this.isOpen) {
      this.open(false);
    } else {
      this.close(false);
    }
  }

  toggle() {
    if (this.isOpen) {
      this.close(true);
    } else {
      this.open(true);
    }
  }
  open(animate) {
    if (animate) {
      this.outerContainer.slideDown();
    } else {
      this.outerContainer.show();
    }
    this.addButton.addClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'false');
    this.isOpen = true;
  }
  close(animate) {
    if (animate) {
      this.outerContainer.slideUp();
    } else {
      this.outerContainer.hide();
    }
    this.addButton.removeClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'true');
    this.isOpen = false;
  }
}

class StreamBlock {
  constructor(blockDef, placeholder, prefix, initialState) {
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

    this.children = [];
    this.menus = [];
    this.blockCounter = 0;
    this.countInput = dom.find('[data-streamfield-stream-count]');
    this.streamContainer = dom.find('[data-streamfield-stream-container]');
    this.setState(initialState || []);
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
          onclick: (blockType, newIndex) => {
            this.insertFromMenu(blockType, newIndex);
          },
        }
      )
    ];
  }

  insert({ type, value, id }, index) {
    const blockDef = this.blockDef.childBlockDefsByName[type];
    const prefix = this.prefix + '-' + this.blockCounter;
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
      this.menus[i].index = i + 1;
    }

    const child = new StreamChild(blockDef, blockPlaceholder, prefix, index, id, value);
    this.children.splice(index, 0, child);

    const menu = new StreamBlockMenu(
      menuPlaceholder, this.blockDef.groupedChildBlockDefs, {
        index: index + 1,
        isOpen: false,
        onclick: (blockType, newIndex) => {
          this.insertFromMenu(blockType, newIndex);
        },
      }
    );
    this.menus.splice(index + 1, 0, menu);

    this.countInput.val(this.children.length);
    return child;
  }

  insertFromMenu(blockType, index) {
    /* handle selecting an item from the 'add block' menu */
    const newBlock = this.insert({
      type: blockType,
      value: this.blockDef.initialChildStates[blockType],
    }, index);
    newBlock.focus();
  }

  setState(values) {
    this.clear();
    values.forEach((val, i) => {
      this.insert(val, i);
    });
    if (values.length === 0) {
      /* for an empty list, begin with the menu open */
      this.menus[0].open(false);
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

class StreamBlockDefinition {
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

  render(placeholder, prefix, initialState) {
    return new StreamBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);
