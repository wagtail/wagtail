/* global $ */

class BoundWidget {
  constructor(element, name, idForLabel, initialState, parentCapabilities) {
    var selector = ':input[name="' + name + '"]';
    this.input = element.find(selector).addBack(selector); // find, including element itself
    this.idForLabel = idForLabel;
    this.setState(initialState);
    this.parentCapabilities = parentCapabilities || new Map();
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

  getTextLabel(opts) {
    const val = this.getValue();
    if (typeof val !== 'string') return null;
    const maxLength = opts && opts.maxLength;
    if (maxLength && val.length > maxLength) {
      return val.substring(0, maxLength - 1) + '…';
    }
    return val;
  }

  focus() {
    this.input.focus();
  }

  setCapabilityOptions(capability, options) {
    Object.assign(this.parentCapabilities.get(capability), options);
  }
}

class Widget {
  constructor(html, idPattern) {
    this.html = html;
    this.idPattern = idPattern;
  }

  boundWidgetClass = BoundWidget;

  render(placeholder, name, id, initialState, parentCapabilities) {
    var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    var idForLabel = this.idPattern.replace(/__ID__/g, id);
    var dom = $(html);
    $(placeholder).replaceWith(dom);
    // eslint-disable-next-line new-cap
    return new this.boundWidgetClass(
      dom,
      name,
      idForLabel,
      initialState,
      parentCapabilities,
    );
  }
}
window.telepath.register('wagtail.widgets.Widget', Widget);

class BoundCheckboxInput extends BoundWidget {
  getValue() {
    return this.input.is(':checked');
  }

  getState() {
    return this.input.is(':checked');
  }

  setState(state) {
    // if false, set attribute value to null to remove it
    this.input.attr('checked', state || null);
  }
}

class CheckboxInput extends Widget {
  boundWidgetClass = BoundCheckboxInput;
}
window.telepath.register('wagtail.widgets.CheckboxInput', CheckboxInput);

class BoundRadioSelect {
  constructor(element, name, idForLabel, initialState) {
    this.element = element;
    this.name = name;
    this.idForLabel = idForLabel;
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

class BoundSelect extends BoundWidget {
  getTextLabel() {
    return this.input.find(':selected').text();
  }
}

class Select extends Widget {
  boundWidgetClass = BoundSelect;
}
window.telepath.register('wagtail.widgets.Select', Select);

class PageChooser {
  constructor(html, idPattern, config) {
    this.html = html;
    this.idPattern = idPattern;
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
  render(placeholder, name, id, initialState, parentCapabilities) {
    const boundWidget = super.render(
      placeholder,
      name,
      id,
      initialState,
      parentCapabilities,
    );
    window.autosize($('#' + id));
    return boundWidget;
  }
}
window.telepath.register(
  'wagtail.widgets.AdminAutoHeightTextInput',
  AdminAutoHeightTextInput,
);

class DraftailRichTextArea {
  constructor(options) {
    this.options = options;
  }

  render(container, name, id, initialState, parentCapabilities) {
    const originalOptions = this.options;
    const options = { ...originalOptions };
    const capabilities = parentCapabilities || new Map();
    const split = capabilities.get('split');
    if (split) {
      options.controls = options.controls ? [...options.controls] : [];
      options.controls.push(
        // eslint-disable-next-line no-undef
        draftail.getSplitControl(split.fn, !!split.enabled),
      );
    }
    const input = document.createElement('input');
    input.type = 'hidden';
    input.id = id;
    input.name = name;

    // If the initialState is an EditorState, rather than serialized rawContentState, it's
    // easier for us to initialize the widget blank and then setState to the correct state
    const initialiseBlank = !!initialState.getCurrentContent;
    input.value = initialiseBlank ? 'null' : initialState;
    container.appendChild(input);
    // eslint-disable-next-line no-undef
    const [currentOptions, setOptions] = draftail.initEditor(
      '#' + id,
      options,
      document.currentScript,
    );

    const boundDraftail = {
      getValue() {
        return input.value;
      },
      getState() {
        return input.draftailEditor.getEditorState();
      },
      setState(editorState) {
        input.draftailEditor.onChange(editorState);
      },
      getTextLabel(opts) {
        const maxLength = opts && opts.maxLength;
        if (!input.value) return '';
        const value = JSON.parse(input.value);
        if (!value || !value.blocks) return '';

        let result = '';
        for (const block of value.blocks) {
          if (block.text) {
            result += result ? ' ' + block.text : block.text;
            if (maxLength && result.length > maxLength) {
              return result.substring(0, maxLength - 1) + '…';
            }
          }
        }
        return result;
      },
      focus: () => {
        setTimeout(() => {
          input.draftailEditor.focus();
        }, 50);
      },
      setCapabilityOptions(capability, capabilityOptions) {
        const newCapability = Object.assign(
          capabilities.get(capability),
          capabilityOptions,
        );
        if (capability === 'split') {
          setOptions({
            ...currentOptions,
            controls: [
              ...(originalOptions || []),
              {
                // eslint-disable-next-line no-undef
                block: draftail.getSplitControl(
                  newCapability.fn,
                  !!newCapability.enabled,
                ),
              },
            ],
          });
        }
      },
    };

    if (initialiseBlank) {
      boundDraftail.setState(initialState);
    }

    return boundDraftail;
  }
}
window.telepath.register(
  'wagtail.widgets.DraftailRichTextArea',
  DraftailRichTextArea,
);

class BaseDateTimeWidget extends Widget {
  constructor(options) {
    this.options = options;
  }

  render(placeholder, name, id, initialState) {
    const element = document.createElement('input');
    element.type = 'text';
    element.name = name;
    element.id = id;
    placeholder.replaceWith(element);

    this.initChooserFn(id, this.options);

    const widget = {
      getValue() {
        return element.value;
      },
      getState() {
        return element.value;
      },
      setState(state) {
        element.value = state;
      },
      focus(opts) {
        // focusing opens the date picker, so don't do this if it's a 'soft' focus
        if (opts && opts.soft) return;
        element.focus();
      },
      idForLabel: id,
    };
    widget.setState(initialState);
    return widget;
  }
}

class AdminDateInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateChooser;
}
window.telepath.register('wagtail.widgets.AdminDateInput', AdminDateInput);

class AdminTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initTimeChooser;
}
window.telepath.register('wagtail.widgets.AdminTimeInput', AdminTimeInput);

class AdminDateTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateTimeChooser;
}
window.telepath.register(
  'wagtail.widgets.AdminDateTimeInput',
  AdminDateTimeInput,
);

class ValidationError {
  constructor(messages) {
    this.messages = messages;
  }
}
window.telepath.register('wagtail.errors.ValidationError', ValidationError);
