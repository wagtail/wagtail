/* global $ */
import { gettext } from '../../../utils/gettext';

class BoundWidget {
  constructor(
    element,
    name,
    idForLabel,
    initialState,
    parentCapabilities,
    options,
  ) {
    var selector = ':input[name="' + name + '"]';
    this.input = element.find(selector).addBack(selector); // find, including element itself
    this.idForLabel = idForLabel;
    this.setState(initialState);
    this.parentCapabilities = parentCapabilities || new Map();
    this.options = options;
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

  render(
    placeholder,
    name,
    id,
    initialState,
    parentCapabilities,
    options = {},
  ) {
    var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    var idForLabel = this.idPattern.replace(/__ID__/g, id);
    var dom = $(html);

    // Add any extra attributes we received to the HTML of the widget
    if (typeof options?.attributes === 'object') {
      Object.entries(options.attributes).forEach(([key, value]) => {
        dom.attr(key, value);
      });
    }
    $(placeholder).replaceWith(dom);
    // eslint-disable-next-line new-cap
    return new this.boundWidgetClass(
      dom,
      name,
      idForLabel,
      initialState,
      parentCapabilities,
      options,
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

class DraftailInsertBlockCommand {
  /* Definition for a command in the Draftail context menu that inserts a block.
   * Constructor args:
   * widget - the bound Draftail widget
   * blockDef - block definition for the block to be inserted
   * addSibling, split - capability descriptors from the containing block's capabilities definition
   */
  constructor(widget, blockDef, addSibling, split) {
    this.widget = widget;
    this.blockDef = blockDef;
    this.addSibling = addSibling;
    this.split = split;

    this.blockMax = addSibling.getBlockMax(blockDef.name);
    this.icon = blockDef.meta.icon;
    this.description = blockDef.meta.label;
    this.type = blockDef.name;
  }

  render({ option }) {
    // If the specific block has a limit, render the current number/max alongside the description
    const limitText =
      typeof blockMax === 'number'
        ? ` (${this.addSibling.getBlockCount(this.blockDef.name)}/${
            this.blockMax
          })`
        : '';
    return `${option.description}${limitText}`;
  }

  onSelect({ editorState }) {
    const result = window.draftail.splitState(
      window.draftail.DraftUtils.removeCommandPalettePrompt(editorState),
    );
    if (result.stateAfter.getCurrentContent().hasText()) {
      // There is content after the insertion point, so need to split the existing block.
      // Run the split after a timeout to circumvent potential race condition.
      setTimeout(() => {
        if (result) {
          this.split.fn(
            result.stateBefore,
            result.stateAfter,
            result.shouldMoveCommentFn,
          );
        }
        // setTimeout required to stop Draftail from giving itself focus again
        setTimeout(() => {
          this.addSibling.fn({ type: this.blockDef.name });
        }, 20);
      }, 50);
    } else {
      // Set the current block's content to the 'before' state, to remove the '/' separator and
      // reset the editor state (closing the context menu)
      this.widget.setState(result.stateBefore);
      // setTimeout required to stop Draftail from giving itself focus again
      setTimeout(() => {
        this.addSibling.fn({ type: this.blockDef.name });
      }, 20);
    }
  }
}

class DraftailSplitCommand {
  /* Definition for a command in the Draftail context menu that splits the block.
   * Constructor args:
   * widget - the bound Draftail widget
   * split - capability descriptor from the containing block's capabilities definition
   */
  constructor(widget, split) {
    this.widget = widget;
    this.split = split;
    this.description = gettext('Split block');
  }

  icon = 'cut';
  type = 'split';

  onSelect({ editorState }) {
    const result = window.draftail.splitState(
      window.draftail.DraftUtils.removeCommandPalettePrompt(editorState),
    );
    // Run the split after a timeout to circumvent potential race condition.
    setTimeout(() => {
      if (result) {
        this.split.fn(
          result.stateBefore,
          result.stateAfter,
          result.shouldMoveCommentFn,
        );
      }
    }, 50);
  }
}

class BoundDraftailWidget {
  constructor(input, options, parentCapabilities) {
    this.input = input;
    this.capabilities = new Map(parentCapabilities);
    this.options = options;

    // eslint-disable-next-line no-undef
    const [, setOptions] = draftail.initEditor(
      '#' + this.input.id,
      this.getFullOptions(),
      document.currentScript,
    );
    this.setDraftailOptions = setOptions;
  }

  getValue() {
    return this.input.value;
  }

  getState() {
    return this.input.draftailEditor.getEditorState();
  }

  setState(editorState) {
    this.input.draftailEditor.onChange(editorState);
  }

  getTextLabel(opts) {
    const maxLength = opts && opts.maxLength;
    if (!this.input.value) return '';
    const value = JSON.parse(this.input.value);
    if (!value || !value.blocks) return '';

    let result = '';
    // eslint-disable-next-line no-restricted-syntax
    for (const block of value.blocks) {
      if (block.text) {
        result += result ? ' ' + block.text : block.text;
        if (maxLength && result.length > maxLength) {
          return result.substring(0, maxLength - 1) + '…';
        }
      }
    }
    return result;
  }

  focus() {
    setTimeout(() => {
      this.input.draftailEditor.focus();
    }, 50);
  }

  setCapabilityOptions(capability, capabilityOptions) {
    const newCapability = Object.assign(
      this.capabilities.get(capability),
      capabilityOptions,
    );
    this.capabilities.set(capability, newCapability);
    this.setDraftailOptions(this.getFullOptions());
  }

  /**
   * Given a mapping of the capabilities supported by this widget's container,
   * return the options overrides that enable additional widget functionality
   * (e.g. splitting or adding additional blocks).
   * Non-context-dependent Draftail options are available here as this.options.
   */
  getCapabilityOptions(parentCapabilities) {
    const options = {};
    const capabilities = parentCapabilities;
    const split = capabilities.get('split');
    const addSibling = capabilities.get('addSibling');
    let blockCommands = [];
    if (split) {
      const blockGroups =
        addSibling && addSibling.enabled && split.enabled
          ? addSibling.blockGroups
          : [];
      // Create commands for splitting + inserting a block. This requires both the split
      // and addSibling capabilities to be available and enabled
      blockCommands = blockGroups.map(([group, blocks]) => {
        const blockControls = blocks.map(
          (blockDef) =>
            new DraftailInsertBlockCommand(this, blockDef, addSibling, split),
        );
        return {
          label: group || gettext('Blocks'),
          type: `streamfield-${group}`,
          items: blockControls,
        };
      });

      if (split.enabled) {
        blockCommands.push({
          label: 'Actions',
          type: 'custom-actions',
          items: [new DraftailSplitCommand(this, split)],
        });
      }
    }

    options.commands = [
      {
        type: 'blockTypes',
      },
      {
        type: 'entityTypes',
      },
      ...blockCommands,
    ];

    return options;
  }

  getFullOptions() {
    return {
      ...this.options,
      ...this.getCapabilityOptions(this.capabilities),
    };
  }
}

class DraftailRichTextArea {
  constructor(options) {
    this.options = options;
  }

  render(container, name, id, initialState, parentCapabilities, options = {}) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.id = id;
    input.name = name;

    // If the initialState is an EditorState, rather than serialized rawContentState, it's
    // easier for us to initialize the widget blank and then setState to the correct state
    const initialiseBlank = !!initialState.getCurrentContent;
    input.value = initialiseBlank ? 'null' : initialState;
    container.appendChild(input);

    const boundDraftail = new BoundDraftailWidget(
      input,
      { ...this.options, ...options },
      parentCapabilities,
    );

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
    super();
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
