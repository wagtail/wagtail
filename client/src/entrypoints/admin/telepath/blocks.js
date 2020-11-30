/* eslint-disable */
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

    var body = document.getElementById(id);

    // unpack the block definition and value
    var blockDefData = JSON.parse(body.dataset.block);
    var blockDef = telepath.unpack(blockDefData);
    var blockValue = JSON.parse(body.dataset.value);

    // replace the 'body' element with the unpopulated HTML structure for the block
    var block = blockDef.render(body, id);
    // populate the block HTML with the value
    block.setState(blockValue);
}
window.initBlockWidget = initBlockWidget;

class FieldBlock {
    constructor(name, widget, meta) {
        this.name = name;
        this.widget = telepath.unpack(widget);
        this.meta = meta;
    }

    render(placeholder, prefix) {
        var html =$(`
            <div>
                <div class="field-content">
                    <div class="input">
                        <div data-streamfield-widget></div>
                        <span></span>
                    </div>
                    <p class="help"></p>
                    <p class="error-message"></p>
                </div>
            </div>
        `);
        var dom = $(html);
        $(placeholder).replaceWith(dom);
        var widgetElement = dom.find('[data-streamfield-widget]').get(0);
        var boundWidget = this.widget.render(widgetElement, prefix, prefix);
        return {
            'setState': function(state) {
                boundWidget.setState(state);
            },
            'getState': function() {
                boundWidget.getState();
            },
            'getValue': function() {
                boundWidget.getValue();
            },
        };
    }
}
telepath.register('wagtail.blocks.FieldBlock', FieldBlock);


class StructBlock {
    constructor(name, childBlocks, meta) {
        this.name = name;
        this.childBlocks = childBlocks.map((child) => {return telepath.unpack(child);});
        this.meta = meta;
    }

    render(placeholder, prefix) {
        var html = $(`
            <div class="{{ classname }}">
                <span>
                    <div class="help">
                        <span class="icon-help-inverse" aria-hidden="true"></span>
                    </div>
                </span>
            </div>
        `);
        var dom = $(html);
        $(placeholder).replaceWith(dom);

        var boundBlocks = {};
        this.childBlocks.forEach(childBlock => {
            var childHtml = $(`
                <div class="field">
                    <label class="field__label"></label>
                    <div data-streamfield-block></div>
                </div>
            `);
            var childDom = $(childHtml);
            dom.append(childDom);
            var label = childDom.find('.field__label');
            label.text(childBlock.meta.label);
            var childBlockElement = childDom.find('[data-streamfield-block]').get(0);
            var boundBlock = childBlock.render(childBlockElement, prefix + '-' + childBlock.name);
            
            boundBlocks[childBlock.name] = boundBlock;
        });

        return {
            'setState': function(state) {
                for (name in state) {
                    boundBlocks[name].setState(state[name]);
                }
            },
            'getState': function() {
                var state = {};
                for (name in boundBlocks) {
                    state[name] = boundBlocks[name].getState();
                }
                return state;
            },
            'getValue': function() {
                var value = {};
                for (name in boundBlocks) {
                    value[name] = boundBlocks[name].getValue();
                }
                return value;
            },
        };
    }
}
telepath.register('wagtail.blocks.StructBlock', StructBlock);
