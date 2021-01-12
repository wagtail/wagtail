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

    const html = $(`
      <div class="${this.blockDef.meta.classname || ''}">
        <div class="field-content">
          <div class="input">
            <div data-streamfield-widget></div>
            <span></span>
          </div>
        </div>
      </div>
    `);
    const dom = $(html);
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

    const html = $(`
      <div class="${this.blockDef.meta.classname || ''}">
      </div>
    `);
    const dom = $(html);
    $(placeholder).replaceWith(dom);

    this.childBlocks = {};
    this.blockDef.childBlockDefs.forEach(childBlockDef => {
      const childHtml = $(`
        <div class="field">
          <label class="field__label">${childBlockDef.meta.label}</label>
          <div data-streamfield-block></div>
        </div>
      `);
      const childDom = $(childHtml);
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

    const html = $(`
      <div class="c-sf-container ${this.blockDef.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
        <button type="button" title="Add" data-streamfield-list-add class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
      </div>
    `);

    const dom = $(html);
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
    const childHtml = $(`
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

    const childDom = $(childHtml);
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
}

class ListBlockDefinition {
  constructor(name, childBlockDef, meta) {
    this.name = name;
    this.childBlockDef = childBlockDef;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState) {
    return new ListBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);


class StreamBlock {
  constructor(blockDef, placeholder, prefix, initialState) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;

    const html = $(`
      <div class="c-sf-container ${this.blockDef.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-stream-count value="0">
        <div data-streamfield-stream-container></div>
      </div>
    `);
    const dom = $(html);
    $(placeholder).replaceWith(dom);

    this.childBlocks = [];
    this.countInput = dom.find('[data-streamfield-stream-count]');
    this.streamContainer = dom.find('[data-streamfield-stream-container]');
    this.setState(initialState || []);
  }

  clear() {
    this.countInput.val(0);
    this.streamContainer.empty();
    this.childBlocks = [];
  }

  append(blockData) {
    const blockType = blockData.type;
    const blockDef = this.blockDef.childBlockDefsByName[blockType];

    const index = this.childBlocks.length;
    const childPrefix = this.prefix + '-' + index;
    const childHtml = $(`
      <div aria-hidden="false">
        <input type="hidden" name="${childPrefix}-deleted" value="">
        <input type="hidden" name="${childPrefix}-order" value="${index}">
        <input type="hidden" name="${childPrefix}-type" value="${blockType}">
        <input type="hidden" name="${childPrefix}-id" value="${blockData.id || ''}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${blockDef.meta.icon}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type">${blockDef.meta.label}</span>
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

    const childDom = $(childHtml);
    this.streamContainer.append(childDom);
    const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
    const childBlock = blockDef.render(childBlockElement, childPrefix + '-value', blockData.value);
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
    return this.childBlocks.map(block => ({
      type: block.type,
      val: block.getState(),
      id: null, /* TODO: add this */
    }));
  }

  getValue() {
    return this.childBlocks.map(block => ({
      type: block.type,
      val: block.getValue(),
      id: null, /* TODO: add this */
    }));
  }
}

class StreamBlockDefinition {
  constructor(name, childBlockDefs, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.childBlockDefsByName = {};
    for (let i = 0; i < this.childBlockDefs.length; i++) {
      const blockDef = this.childBlockDefs[i];
      this.childBlockDefsByName[blockDef.name] = blockDef;
    }
    this.meta = meta;
  }

  render(placeholder, prefix, initialState) {
    return new StreamBlock(this, placeholder, prefix, initialState);
  }
}
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);
