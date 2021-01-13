/* eslint-disable indent */

/* global $ */

class BoundWidget {
    constructor(element, name, initialState) {
        var selector = ':input[name="' + name + '"]';
        this.input = element.find(selector).addBack(selector);  // find, including element itself
        this.setState(initialState);
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
    focus() {
        this.input.focus();
    }
}

class Widget {
    constructor(html, idForLabel) {
        this.html = html;
        this.idForLabel = idForLabel;
    }

    boundWidgetClass = BoundWidget;

    render(placeholder, name, id, initialState) {
        var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
        var dom = $(html);
        $(placeholder).replaceWith(dom);
        // eslint-disable-next-line new-cap
        return new this.boundWidgetClass(dom, name, initialState);
    }
}
window.telepath.register('wagtail.widgets.Widget', Widget);


class BoundRadioSelect {
    constructor(element, name, initialState) {
        this.element = element;
        this.name = name;
        this.selector = 'input[name="' + name + '"]:checked';
        this.setState(initialState);
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
    focus() {
        this.element.find('input[name="' + this.name + '"]').focus();
    }
}

class RadioSelect extends Widget {
    boundWidgetClass = BoundRadioSelect;
}
window.telepath.register('wagtail.widgets.RadioSelect', RadioSelect);


class PageChooser {
    constructor(html, idForLabel, config) {
        this.html = html;
        this.idForLabel = idForLabel;
        this.config = config;
    }

    render(placeholder, name, id, initialState) {
        var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
        var dom = $(html);
        $(placeholder).replaceWith(dom);
        /* the chooser object returned by createPageChooser also serves as the JS widget representation */
        // eslint-disable-next-line no-undef
        const chooser = createPageChooser(id, null, this.config);
        chooser.setState(initialState);
        return chooser;
    }
}
window.telepath.register('wagtail.widgets.PageChooser', PageChooser);


class AdminAutoHeightTextInput extends Widget {
    render(placeholder, name, id, initialState) {
        const boundWidget = super.render(placeholder, name, id, initialState);
        window.autosize($(id));
        return boundWidget;
    }
}
window.telepath.register('wagtail.widgets.AdminAutoHeightTextInput', AdminAutoHeightTextInput);


class DraftailRichTextArea {
    constructor(options) {
        this.options = options;
    }

    render(container, name, id, initialState) {
        const options = this.options;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.id = id;
        input.name = name;
        input.value = initialState;
        container.appendChild(input);
        // eslint-disable-next-line no-undef
        draftail.initEditor('#' + id, options, document.currentScript);

        return {
            getValue() {
                return input.value;
            },
            getState() {
                return input.value;
            },
            setState() {
                throw new Error('DraftailRichTextArea.setState is not implemented');
            },
            focus: () => {
                input.draftailEditor.focus();
            },
        };
    }
}
window.telepath.register('wagtail.widgets.DraftailRichTextArea', DraftailRichTextArea);
