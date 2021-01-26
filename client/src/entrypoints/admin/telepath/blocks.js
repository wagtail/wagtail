/* eslint-disable no-warning-comments */

/* global $ */

import { escapeHtml } from '../../../utils/text';


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
  const blockErrors = window.telepath.unpack(JSON.parse(body.dataset.errors));

  // replace the 'body' element with the populated HTML structure for the block
  blockDef.render(body, id, blockValue, blockErrors);
}
window.initBlockWidget = initBlockWidget;


class FieldBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
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
    this.element = dom[0];
    this.widget = this.blockDef.widget.render(widgetElement, prefix, prefix, initialState);
    this.idForLabel = this.widget.idForLabel;

    if (this.blockDef.meta.helpText) {
      const helpElement = document.createElement('p');
      helpElement.classList.add('help');
      helpElement.innerHTML = this.blockDef.meta.helpText;  // unescaped, as per Django conventions
      this.element.querySelector('.field-content').appendChild(helpElement);
    }

    if (initialError) {
      this.setError(initialError);
    }
  }

  setState(state) {
    this.widget.setState(state);
  }

  setError(errorList) {
    this.element.querySelectorAll(':scope > .field-content > .error-message').forEach(element => element.remove());

    if (errorList) {
      this.element.classList.add('error');

      const errorElement = document.createElement('p');
      errorElement.classList.add('error-message');
      errorElement.innerHTML = errorList.map(error => `<span>${escapeHtml(error[0])}</span>`).join('');
      this.element.querySelector('.field-content').appendChild(errorElement);
    } else {
      this.element.classList.remove('error');
    }
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

  render(placeholder, prefix, initialState, initialError) {
    return new FieldBlock(this, placeholder, prefix, initialState, initialError);
  }
}
window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);


class StructBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    const state = initialState || {};
    this.blockDef = blockDef;
    this.type = blockDef.name;

    this.childBlocks = {};

    if (blockDef.meta.formTemplate) {
      const html = blockDef.meta.formTemplate.replace(/__PREFIX__/g, prefix);
      const dom = $(html);
      $(placeholder).replaceWith(dom);
      this.blockDef.childBlockDefs.forEach(childBlockDef => {
        const childBlockElement = dom.find('[data-structblock-child="' + childBlockDef.name + '"]').get(0);
        const childBlock = childBlockDef.render(
          childBlockElement,
          prefix + '-' + childBlockDef.name,
          state[childBlockDef.name],
          initialError?.blockErrors[childBlockDef.name]
        );
        this.childBlocks[childBlockDef.name] = childBlock;
      });
    } else {
      const dom = $(`
        <div class="${this.blockDef.meta.classname || ''}">
        </div>
      `);
      $(placeholder).replaceWith(dom);

      if (this.blockDef.meta.helpText) {
        // help text is left unescaped as per Django conventions
        dom.append(`
          <span>
            <div class="help">
              ${this.blockDef.meta.helpIcon}
              ${this.blockDef.meta.helpText}
            </div>
          </span>
        `);
      }

      this.blockDef.childBlockDefs.forEach(childBlockDef => {
        const childDom = $(`
          <div class="field ${childBlockDef.meta.required ? 'required' : ''}">
            <label class="field__label">${childBlockDef.meta.label}</label>
            <div data-streamfield-block></div>
          </div>
        `);
        dom.append(childDom);
        const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
        const labelElement = childDom.find('label').get(0);
        const childBlock = childBlockDef.render(
          childBlockElement,
          prefix + '-' + childBlockDef.name,
          state[childBlockDef.name],
          initialError?.blockErrors[childBlockDef.name]
        );

        this.childBlocks[childBlockDef.name] = childBlock;
        if (childBlock.idForLabel) {
          labelElement.setAttribute('for', childBlock.idForLabel);
        }
      });
    }
  }

  setState(state) {
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in state) {
      this.childBlocks[name].setState(state[name]);
    }
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];

    // eslint-disable-next-line no-restricted-syntax
    for (const blockName in error.blockErrors) {
      if (error.blockErrors.hasOwnProperty(blockName)) {
        this.childBlocks[blockName].setError(error.blockErrors[blockName]);
      }
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

  render(placeholder, prefix, initialState, initialError) {
    return new StructBlock(this, placeholder, prefix, initialState, initialError);
  }
}
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);

class StructBlockValidationError {
  constructor(blockErrors) {
    this.blockErrors = blockErrors;
  }
}

window.telepath.register('wagtail.blocks.StructBlockValidationError', StructBlockValidationError);


class ListChild {
  /*
  wrapper for an item inside a ListBlock
  */
  constructor(blockDef, placeholder, prefix, index, initialState, opts) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;

    this.onRequestDelete = opts && opts.onRequestDelete;

    const dom = $(`
      <div id="${this.prefix}-container" aria-hidden="false">
        <input type="hidden" data-listblock-deleted id="${this.prefix}-deleted" name="${this.prefix}-deleted" value="">
        <input type="hidden"
          data-listblock-index id="${this.prefix}-order" name="${this.prefix}-order" value="${index}">
        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${this.blockDef.meta.icon}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type"></span>
                  <button type="button" id="${this.prefix}-moveup" class="c-sf-block__actions__single"
                      title="{% trans 'Move up' %}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" id="${this.prefix}-movedown" class="c-sf-block__actions__single"
                      title="{% trans 'Move down' %}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-listblock-delete-button
                      class="c-sf-block__actions__single" title="{% trans 'Delete' %}">
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
    this.block = this.blockDef.render(blockElement, this.prefix + '-value', initialState);

    this.deletedInput = dom.find('[data-listblock-deleted]');
    this.indexInput = dom.find('[data-listblock-index]');

    dom.find('[data-listblock-delete-button]').click(() => {
      if (this.onRequestDelete) this.onRequestDelete(this.index);
    });
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

  setIndex(newIndex) {
    this.index = newIndex;
    this.indexInput.val(newIndex);
  }

  setError(error) {
    this.block.setError(error);
  }

  getState() {
    return this.block.getState();
  }

  getValue() {
    return this.block.getValue();
  }

  focus() {
    this.block.focus();
  }
}

class ListBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
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
      this.append(this.blockDef.initialChildState);
    });
  }

  clear() {
    this.countInput.val(0);
    this.listContainer.empty();
    this.children = [];
  }

  append(value) {
    const index = this.children.length;
    const prefix = this.prefix + '-' + index;
    const placeholder = document.createElement('div');
    this.listContainer.append(placeholder);

    const child = new ListChild(this.blockDef.childBlockDef, placeholder, prefix, index, value, {
      onRequestDelete: (i) => { this.deleteBlock(i); }
    });
    this.children.push(child);
    this.countInput.val(this.children.length);
  }

  deleteBlock(index) {
    this.children[index].markDeleted({ animate: true });
    this.children.splice(index, 1);

    /* index numbers of children / menus above this index now need updating to match
    their array indexes */
    for (let i = index; i < this.children.length; i++) {
      this.children[i].setIndex(i);
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

class ListBlockDefinition {
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
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);

class ListBlockValidationError {
  constructor(blockErrors) {
    this.blockErrors = blockErrors;
  }
}

window.telepath.register('wagtail.blocks.ListBlockValidationError', ListBlockValidationError);


class StreamChild {
  /*
  wrapper for a block inside a StreamBlock, handling StreamBlock-specific metadata
  such as id
  */
  constructor(blockDef, placeholder, prefix, index, id, state, opts) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;

    const animate = opts && opts.animate;
    this.onRequestDelete = opts && opts.onRequestDelete;

    const dom = $(`
      <div aria-hidden="false">
        <input type="hidden" data-streamblock-deleted name="${this.prefix}-deleted" value="">
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
                  <button type="button" data-streamblock-delete-button
                      class="c-sf-block__actions__single" title="{% trans 'Delete' %}">
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
    this.deletedInput = dom.find('[data-streamblock-deleted]');

    dom.find('[data-streamblock-delete-button]').click(() => {
      if (this.onRequestDelete) this.onRequestDelete(this.index);
    });

    if (animate) {
      dom.hide().slideDown();
    }
  }

  markDeleted(opts) {
    this.deletedInput.val('1');
    if (opts && opts.animate) {
      $(this.element).slideUp().dequeue()
        .fadeOut()
        .attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }
  }

  setIndex(newIndex) {
    this.index = newIndex;
    this.indexInput.val(newIndex);
  }

  setError(errorList) {
    this.block.setError(errorList);
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

class StreamBlock {
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

  render(placeholder, prefix, initialState, initialError) {
    return new StreamBlock(this, placeholder, prefix, initialState, initialError);
  }
}
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);

class StreamBlockValidationError {
  constructor(nonBlockErrors, blockErrors) {
    this.nonBlockErrors = nonBlockErrors;
    this.blockErrors = blockErrors;
  }
}

window.telepath.register('wagtail.blocks.StreamBlockValidationError', StreamBlockValidationError);
