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

  // replace the 'body' element with the unpopulated HTML structure for the block
  const block = blockDef.render(body, id);
  // populate the block HTML with the value
  block.setState(blockValue);
}
window.initBlockWidget = initBlockWidget;

class FieldBlock {
  constructor(name, widget, meta) {
    this.name = name;
    this.widget = window.telepath.unpack(widget);
    this.meta = meta;
  }

  render(placeholder, prefix) {
    const html = $(`
      <div>
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
    const boundWidget = this.widget.render(widgetElement, prefix, prefix);
    return {
      type: this.name,
      setState(state) {
        boundWidget.setState(state);
      },
      getState() {
        boundWidget.getState();
      },
      getValue() {
        boundWidget.getValue();
      },
    };
  }
}
window.telepath.register('wagtail.blocks.FieldBlock', FieldBlock);


class StructBlock {
  constructor(name, childBlocks, meta) {
    this.name = name;
    this.childBlocks = childBlocks.map((child) => window.telepath.unpack(child));
    this.meta = meta;
  }

  render(placeholder, prefix) {
    const html = $(`
      <div class="${this.meta.classname || ''}">
      </div>
    `);
    const dom = $(html);
    $(placeholder).replaceWith(dom);

    const boundBlocks = {};
    this.childBlocks.forEach(childBlock => {
      const childHtml = $(`
        <div class="field">
          <label class="field__label">${childBlock.meta.label}</label>
          <div data-streamfield-block></div>
        </div>
      `);
      const childDom = $(childHtml);
      dom.append(childDom);
      const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
      const boundBlock = childBlock.render(childBlockElement, prefix + '-' + childBlock.name);

      boundBlocks[childBlock.name] = boundBlock;
    });

    return {
      type: this.name,
      setState(state) {
        // eslint-disable-next-line guard-for-in, no-restricted-syntax
        for (const name in state) {
          boundBlocks[name].setState(state[name]);
        }
      },
      getState() {
        const state = {};
        // eslint-disable-next-line guard-for-in, no-restricted-syntax
        for (const name in boundBlocks) {
          state[name] = boundBlocks[name].getState();
        }
        return state;
      },
      getValue() {
        const value = {};
        // eslint-disable-next-line guard-for-in, no-restricted-syntax
        for (const name in boundBlocks) {
          value[name] = boundBlocks[name].getValue();
        }
        return value;
      },
    };
  }
}
window.telepath.register('wagtail.blocks.StructBlock', StructBlock);


class ListBlock {
  constructor(name, childBlock, meta) {
    this.name = name;
    this.childBlock = window.telepath.unpack(childBlock);
    this.meta = meta;
  }

  render(placeholder, prefix) {
    const html = $(`
      <div class="c-sf-container ${this.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-list-count value="0">

        <div data-streamfield-list-container></div>
        <button type="button" title="Add" data-streamfield-list-add class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
      </div>
    `);
    const dom = $(html);
    $(placeholder).replaceWith(dom);

    let boundBlocks = [];
    const countInput = dom.find('[data-streamfield-list-count]');
    const listContainer = dom.find('[data-streamfield-list-container]');

    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const self = this;

    return {
      type: this.name,
      setState(values) {
        countInput.val(values.length);
        boundBlocks = [];
        listContainer.empty();
        values.forEach((val, index) => {
          const childPrefix = prefix + '-' + index;
          const childHtml = $(`
            <div id="${childPrefix}-container" aria-hidden="false">
              <input type="hidden" id="${childPrefix}-deleted" name="${childPrefix}-deleted" value="">
              <input type="hidden" id="${childPrefix}-order" name="${childPrefix}-order" value="${index}">
              <div>
                <div class="c-sf-container__block-container">
                  <div class="c-sf-block">
                    <div class="c-sf-block__header">
                      <span class="c-sf-block__header__icon">
                        <i class="icon icon-${self.childBlock.meta.icon}"></i>
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
          listContainer.append(childDom);
          const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
          const boundBlock = self.childBlock.render(childBlockElement, childPrefix + '-value');
          boundBlock.setState(val);
          boundBlocks.push(boundBlock);
        });
      },
      getState() {
        return boundBlocks.map((boundBlock) => boundBlock.getState());
      },
      getValue() {
        return boundBlocks.map((boundBlock) => boundBlock.getValue());
      },
    };
  }
}
window.telepath.register('wagtail.blocks.ListBlock', ListBlock);


class StreamBlock {
  constructor(name, childBlocks, meta) {
    this.name = name;
    this.childBlocks = childBlocks.map((child) => window.telepath.unpack(child));
    this.childBlocksByName = {};
    for (let i = 0; i < this.childBlocks.length; i++) {
      const block = this.childBlocks[i];
      this.childBlocksByName[block.name] = block;
    }
    this.meta = meta;
  }

  render(placeholder, prefix) {
    const html = $(`
      <div class="c-sf-container ${this.meta.classname || ''}">
        <input type="hidden" name="${prefix}-count" data-streamfield-stream-count value="0">
        <div data-streamfield-stream-container></div>
      </div>
    `);
    const dom = $(html);
    $(placeholder).replaceWith(dom);
    let boundBlocks = [];
    const countInput = dom.find('[data-streamfield-stream-count]');
    const streamContainer = dom.find('[data-streamfield-stream-container]');

    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const self = this;

    return {
      type: this.name,
      setState(values) {
        countInput.val(values.length);
        streamContainer.empty();
        boundBlocks = [];
        for (let index = 0; index < values.length; index++) {
          const blockData = values[index];
          const blockType = blockData.type;
          const block = self.childBlocksByName[blockType];

          const childPrefix = prefix + '-' + index;
          const childHtml = `
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
                        <i class="icon icon-${block.meta.icon}"></i>
                      </span>
                      <h3 class="c-sf-block__header__title"></h3>
                      <div class="c-sf-block__actions">
                        <span class="c-sf-block__type">${block.meta.label}</span>
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
          `;
          const childDom = $(childHtml);
          streamContainer.append(childDom);
          const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
          const boundBlock = block.render(childBlockElement, childPrefix + '-value');
          boundBlock.setState(blockData.value);
          boundBlocks.push(boundBlock);
        }
      },
      getState() {
        return boundBlocks.map((boundBlock) => ({
          type: boundBlock.type,
          val: boundBlock.getState(),
          id: null, /* TODO: add this */
        }));
      },
      getValue() {
        return boundBlocks.map((boundBlock) => ({
          type: boundBlock.type,
          val: boundBlock.getValue(),
          id: null, /* TODO: add this */
        }));
      },
    };
  }
}
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlock);
