/* eslint-disable indent, vars-on-top, no-warning-comments, max-len */

/* global $ */

class BoundWidget {
    constructor(element, name) {
        var selector = ':input[name="' + name + '"]';
        this.input = element.find(selector).addBack(selector);  // find, including element itself
    }
    getValue() {
        return this.input.val();
    }
    getState() {
        return this.input.val();
    }
    setState(state) {
        this.input.val(state);
    }
}

class Widget {
    constructor(html, idForLabel) {
        this.html = html;
        this.idForLabel = idForLabel;
    }

    static boundWidgetClass = BoundWidget;

    render(placeholder, name, id) {
        var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
        var dom = $(html);
        $(placeholder).replaceWith(dom);
        // eslint-disable-next-line new-cap
        return new this.boundWidgetClass(dom, name);
    }
}
window.telepath.register('wagtail.widgets.Widget', Widget);


class BoundRadioSelect {
    constructor(element, name) {
        this.element = element;
        this.name = name;
        this.selector = 'input[name="' + name + '"]:checked';
    }
    getValue() {
        return this.element.find(this.selector).val();
    }
    getState() {
        return this.element.find(this.selector).val();
    }
    setState(state) {
        this.element.find('input[name="' + this.name + '"]').val([state]);
    }
}

class RadioSelect extends Widget {
    static boundWidgetClass = BoundRadioSelect;
}
window.telepath.register('wagtail.widgets.RadioSelect', RadioSelect);
