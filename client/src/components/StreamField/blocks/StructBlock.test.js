import $ from 'jquery';
import { FieldBlockDefinition } from './FieldBlock';
import { StreamBlockDefinition } from './StreamBlock';
import { BlockGroupDefinition, StructBlockDefinition } from './StructBlock';

window.$ = $;

window.comments = {
  getContentPath: jest.fn(),
};

// Define some callbacks in global scope that can be mocked in tests
let constructor = (_widgetName, _name, _id, _initialState) => {};
let setState = (_widgetName, _state) => {};
let getState = (_widgetName) => {};
let getValue = (_widgetName) => {};
let focus = (_widgetName) => {};

class DummyWidgetDefinition {
  constructor(widgetName) {
    this.widgetName = widgetName;
  }

  render(placeholder, name, id, initialState) {
    const widgetName = this.widgetName;
    constructor(widgetName, { name, id, initialState });

    $(placeholder).replaceWith(
      `<p name="${name}" id="${id}">${widgetName}</p>`,
    );
    return {
      setState(state) {
        setState(widgetName, state);
      },
      getState() {
        getState(widgetName);
        return `state: ${widgetName} - ${name}`;
      },
      getValue() {
        getValue(widgetName);
        return `value: ${widgetName} - ${name}`;
      },
      getTextLabel() {
        return `label: ${name}`;
      },
      focus() {
        focus(widgetName);
      },
      idForLabel: id,
    };
  }
}

describe('telepath: wagtail.blocks.StructBlock', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new StructBlockDefinition(
      'heading_block',
      [
        new FieldBlockDefinition(
          'heading_text',
          new DummyWidgetDefinition('Heading widget'),
          {
            label: 'Heading text',
            required: true,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
            attrs: {
              'data-controller': 'w-custom',
              'data-action': 'click->w-custom#doSomething',
            },
          },
        ),
        new FieldBlockDefinition(
          'size',
          new DummyWidgetDefinition('Size widget'),
          {
            label: 'Size',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--choice_field w-field--select',
            attrs: {
              'data-controller': 'w-other',
              'data-action': 'click->w-other#doSomethingElse',
            },
          },
        ),
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<svg></svg>',
        attrs: {
          'data-controller': 'w-customstruct',
          'data-action': 'click->w-customstruct#doAnotherThing',
        },
        formLayout: new BlockGroupDefinition({
          children: [
            ['heading_text', 'heading_text'],
            ['size', 'size'],
          ],
          settings: [],
        }),
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', {
      heading_text: 'Test heading text',
      size: '123',
    });
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(2);

    expect(constructor.mock.calls[0][0]).toBe('Heading widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-heading_text',
      id: 'the-prefix-heading_text',
      initialState: 'Test heading text',
    });

    expect(constructor.mock.calls[1][0]).toBe('Size widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-size',
      id: 'the-prefix-size',
      initialState: '123',
    });
  });

  test('getValue() calls getValue() on all widgets', () => {
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual({
      heading_text: 'value: Heading widget - the-prefix-heading_text',
      size: 'value: Size widget - the-prefix-size',
    });
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual({
      heading_text: 'state: Heading widget - the-prefix-heading_text',
      size: 'state: Size widget - the-prefix-size',
    });
  });

  test('setState() calls setState() on all widgets', () => {
    boundBlock.setState({
      heading_text: 'Changed heading text',
      size: '456',
    });
    expect(setState.mock.calls.length).toBe(2);
    expect(setState.mock.calls[0][0]).toBe('Heading widget');
    expect(setState.mock.calls[0][1]).toBe('Changed heading text');
    expect(setState.mock.calls[1][0]).toBe('Size widget');
    expect(setState.mock.calls[1][1]).toBe('456');
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Heading widget');
  });

  test('getTextLabel() returns text label of first widget', () => {
    expect(boundBlock.getTextLabel()).toBe('label: the-prefix-heading_text');
  });

  test('setError passes error messages to children', () => {
    boundBlock.setError({
      blockErrors: {
        size: { messages: ['This is too big.'] },
      },
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('setError shows non-block errors', () => {
    boundBlock.setError({
      messages: ['This is just generally wrong.'],
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StructBlock with collapsible panel', () => {
  let boundBlock;

  const setup = (collapsed = true) => {
    // Define a test block
    const blockDef = new StructBlockDefinition(
      'settings_block',
      [
        new FieldBlockDefinition(
          'accent_color',
          new DummyWidgetDefinition('Accent color widget'),
          {
            label: 'Accent color',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
          },
        ),
        new FieldBlockDefinition(
          'font_size',
          new DummyWidgetDefinition('Font size widget'),
          {
            label: 'Font size',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--choice_field w-field--select',
          },
        ),
      ],
      {
        label: 'Settings block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'configure how the block is <strong>displayed</strong>',
        helpIcon: '<svg></svg>',
        collapsed,
        formLayout: new BlockGroupDefinition({
          children: [
            ['accent_color', 'accent_color'],
            ['font_size', 'font_size'],
          ],
          settings: [],
        }),
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', {
      accent_color: 'Test accent color',
      font_size: '16px',
    });
  };

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    setup();
  });

  test('it renders correctly with initially collapsed state', () => {
    expect(document.body.innerHTML).toMatchSnapshot();

    // Check that the panel can be expanded by clicking the toggle button
    const button = document.querySelector('[data-panel-toggle]');
    expect(button).toBeTruthy();
    button.click();

    // Check that the panel is now expanded
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('it renders correctly with initially expanded state', () => {
    // Setup with initially expanded state (collapsed = False)
    setup(false);

    expect(document.body.innerHTML).toMatchSnapshot();

    // Check that the panel can be expanded by clicking the toggle button
    const button = document.querySelector('[data-panel-toggle]');
    expect(button).toBeTruthy();
    button.click();

    // Check that the panel is now expanded
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(2);

    expect(constructor.mock.calls[0][0]).toBe('Accent color widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-accent_color',
      id: 'the-prefix-accent_color',
      initialState: 'Test accent color',
    });

    expect(constructor.mock.calls[1][0]).toBe('Font size widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-font_size',
      id: 'the-prefix-font_size',
      initialState: '16px',
    });
  });

  test('getValue() calls getValue() on all widgets', () => {
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual({
      accent_color: 'value: Accent color widget - the-prefix-accent_color',
      font_size: 'value: Font size widget - the-prefix-font_size',
    });
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual({
      accent_color: 'state: Accent color widget - the-prefix-accent_color',
      font_size: 'state: Font size widget - the-prefix-font_size',
    });
  });

  test('setState() calls setState() on all widgets', () => {
    boundBlock.setState({
      accent_color: 'Changed accent color',
      font_size: '456',
    });
    expect(setState.mock.calls.length).toBe(2);
    expect(setState.mock.calls[0][0]).toBe('Accent color widget');
    expect(setState.mock.calls[0][1]).toBe('Changed accent color');
    expect(setState.mock.calls[1][0]).toBe('Font size widget');
    expect(setState.mock.calls[1][1]).toBe('456');
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Accent color widget');
  });

  test('getTextLabel() returns text label of first widget', () => {
    expect(boundBlock.getTextLabel()).toBe('label: the-prefix-accent_color');
  });

  test('setError passes error messages to children', () => {
    boundBlock.setError({
      blockErrors: {
        font_size: { messages: ['This is too big.'] },
      },
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('setError shows non-block errors', () => {
    boundBlock.setError({
      messages: ['This is just generally wrong.'],
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StructBlock with nested collapsible panel', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const settingsBlockDef = new StructBlockDefinition(
      'settings',
      [
        new FieldBlockDefinition(
          'accent_color',
          new DummyWidgetDefinition('Accent color widget'),
          {
            label: 'Accent color',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
          },
        ),
        new FieldBlockDefinition(
          'font_size',
          new DummyWidgetDefinition('Font size widget'),
          {
            label: 'Font size',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--choice_field w-field--select',
          },
        ),
      ],
      {
        label: 'Settings block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'configure how the block is <strong>displayed</strong>',
        helpIcon: '<svg></svg>',
        collapsed: true, // Initially collapsed
        formLayout: new BlockGroupDefinition({
          children: [
            ['accent_color', 'accent_color'],
            ['font_size', 'font_size'],
          ],
          settings: [],
        }),
      },
    );

    const blockDef = new StructBlockDefinition(
      'heading_block',
      [
        new FieldBlockDefinition(
          'heading_text',
          new DummyWidgetDefinition('Heading widget'),
          {
            label: 'Heading text',
            required: true,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
          },
        ),
        new FieldBlockDefinition(
          'size',
          new DummyWidgetDefinition('Size widget'),
          {
            label: 'Size',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--choice_field w-field--select',
          },
        ),
        settingsBlockDef,
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<svg></svg>',
        formLayout: new BlockGroupDefinition({
          children: [
            ['heading_text', 'heading_text'],
            ['size', 'size'],
            ['settings', 'settings'],
          ],
          settings: [],
        }),
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', {
      heading_text: 'Test heading text',
      size: '123',
      settings: {
        accent_color: 'Test accent color',
        font_size: '16px',
      },
    });
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();

    // Check that the panel can be expanded by clicking the toggle button
    const button = document.querySelector('[data-panel-toggle]');
    expect(button).toBeTruthy();
    button.click();

    // Check that the panel is now expanded
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(4);

    expect(constructor.mock.calls[0][0]).toBe('Heading widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-heading_text',
      id: 'the-prefix-heading_text',
      initialState: 'Test heading text',
    });

    expect(constructor.mock.calls[1][0]).toBe('Size widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-size',
      id: 'the-prefix-size',
      initialState: '123',
    });
  });

  test('getValue() calls getValue() on all widgets', () => {
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(4);
    expect(value).toEqual({
      heading_text: 'value: Heading widget - the-prefix-heading_text',
      size: 'value: Size widget - the-prefix-size',
      settings: {
        accent_color:
          'value: Accent color widget - the-prefix-settings-accent_color',
        font_size: 'value: Font size widget - the-prefix-settings-font_size',
      },
    });
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(4);
    expect(state).toEqual({
      heading_text: 'state: Heading widget - the-prefix-heading_text',
      size: 'state: Size widget - the-prefix-size',
      settings: {
        accent_color:
          'state: Accent color widget - the-prefix-settings-accent_color',
        font_size: 'state: Font size widget - the-prefix-settings-font_size',
      },
    });
  });

  test('setState() calls setState() on all widgets', () => {
    boundBlock.setState({
      heading_text: 'Changed heading text',
      size: '456',
    });
    expect(setState.mock.calls.length).toBe(2);
    expect(setState.mock.calls[0][0]).toBe('Heading widget');
    expect(setState.mock.calls[0][1]).toBe('Changed heading text');
    expect(setState.mock.calls[1][0]).toBe('Size widget');
    expect(setState.mock.calls[1][1]).toBe('456');
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Heading widget');
  });

  test('getTextLabel() returns text label of first widget', () => {
    expect(boundBlock.getTextLabel()).toBe('label: the-prefix-heading_text');
  });

  test('setError passes error messages to children', () => {
    boundBlock.setError({
      blockErrors: {
        size: { messages: ['This is too big.'] },
      },
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('setError shows non-block errors', () => {
    boundBlock.setError({
      messages: ['This is just generally wrong.'],
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StructBlock with formTemplate', () => {
  let boundBlock;
  let blockDefWithBadLabelFormat;
  let blockDefWithEmptyLabelFormat;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockOpts = {
      label: 'Heading block',
      required: false,
      icon: 'title',
      formTemplate: `<div class="custom-form-template">
        <p>here comes the first field:</p>
        <div data-structblock-child="heading_text"></div>
        <p>and here is the second:</p>
        <div data-structblock-child="size"></div>
      </div>`,
      labelFormat: '{heading_text} - {size}',
      formLayout: new BlockGroupDefinition({
        children: [
          ['heading_text', 'heading_text'],
          ['size', 'size'],
        ],
        settings: [],
      }),
    };
    const headingTextBlockDef = new FieldBlockDefinition(
      'heading_text',
      new DummyWidgetDefinition('Heading widget'),
      {
        label: 'Heading text',
        required: true,
        icon: 'placeholder',
        classname: 'w-field w-field--char_field w-field--text_input',
      },
    );
    const sizeBlockDef = new FieldBlockDefinition(
      'size',
      new DummyWidgetDefinition('Size widget'),
      {
        label: 'Size',
        required: false,
        icon: 'placeholder',
        classname: 'w-field w-field--choice_field w-field--select',
      },
    );

    const blockDef = new StructBlockDefinition(
      'heading_block',
      [headingTextBlockDef, sizeBlockDef],
      blockOpts,
    );
    blockDefWithBadLabelFormat = new StructBlockDefinition(
      'heading_block',
      [headingTextBlockDef, sizeBlockDef],
      { ...blockOpts, labelFormat: '{bad_variable} - {size}' },
    );
    blockDefWithEmptyLabelFormat = new StructBlockDefinition(
      'heading_block',
      [headingTextBlockDef, sizeBlockDef],
      { ...blockOpts, labelFormat: '' },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', {
      heading_text: 'Test heading text',
      size: '123',
    });
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(2);

    expect(constructor.mock.calls[0][0]).toBe('Heading widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-heading_text',
      id: 'the-prefix-heading_text',
      initialState: 'Test heading text',
    });

    expect(constructor.mock.calls[1][0]).toBe('Size widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-size',
      id: 'the-prefix-size',
      initialState: '123',
    });
  });

  test('getValue() calls getValue() on all widgets', () => {
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual({
      heading_text: 'value: Heading widget - the-prefix-heading_text',
      size: 'value: Size widget - the-prefix-size',
    });
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual({
      heading_text: 'state: Heading widget - the-prefix-heading_text',
      size: 'state: Size widget - the-prefix-size',
    });
  });

  test('setState() calls setState() on all widgets', () => {
    boundBlock.setState({
      heading_text: 'Changed heading text',
      size: '456',
    });
    expect(setState.mock.calls.length).toBe(2);
    expect(setState.mock.calls[0][0]).toBe('Heading widget');
    expect(setState.mock.calls[0][1]).toBe('Changed heading text');
    expect(setState.mock.calls[1][0]).toBe('Size widget');
    expect(setState.mock.calls[1][1]).toBe('456');
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Heading widget');
  });

  test('getTextLabel() returns text label according to labelFormat', () => {
    expect(boundBlock.getTextLabel()).toBe(
      'label: the-prefix-heading_text - label: the-prefix-size',
    );
  });

  test('getTextLabel() gracefully handles bad variables in labelFormat', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDefWithBadLabelFormat.render(
      $('#placeholder'),
      'the-prefix',
      {
        heading_text: 'Test heading text',
        size: '123',
      },
    );
    expect(boundBlock.getTextLabel()).toBe(' - label: the-prefix-size');
  });

  test('getTextLabel() allows empty labelFormat', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDefWithEmptyLabelFormat.render(
      $('#placeholder'),
      'the-prefix',
      {
        heading_text: 'Test heading text',
        size: '123',
      },
    );
    expect(boundBlock.getTextLabel()).toBe('');
  });
});

describe('telepath: wagtail.blocks.StructBlock with formLayout', () => {
  let boundBlock;

  const setup = (opts, nestedOpts) => {
    // Define a test block
    const blockDef = new StructBlockDefinition(
      'hero',
      [
        new FieldBlockDefinition(
          'text',
          new DummyWidgetDefinition('Text content'),
          {
            label: 'Text content',
            required: true,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
          },
        ),
        new FieldBlockDefinition('url', new DummyWidgetDefinition('Link'), {
          label: 'Link',
          required: true,
          icon: 'placeholder',
          classname: 'w-field w-field--url_field w-field--text_input',
        }),
        new FieldBlockDefinition(
          'accent_color',
          new DummyWidgetDefinition('Accent color widget'),
          {
            label: 'Accent color',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--char_field w-field--text_input',
          },
        ),
        new FieldBlockDefinition(
          'font_size',
          new DummyWidgetDefinition('Font size widget'),
          {
            label: 'Font size',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--choice_field w-field--select',
          },
        ),
        new FieldBlockDefinition(
          'shown',
          new DummyWidgetDefinition('Shown widget'),
          {
            label: 'Shown',
            required: false,
            icon: 'placeholder',
            classname: 'w-field w-field--boolean_field w-field--checkbox_input',
          },
        ),
        // Nested StructBlock
        new StructBlockDefinition(
          'captioned_image',
          [
            new FieldBlockDefinition(
              'image',
              new DummyWidgetDefinition('Image widget'),
              {
                label: 'Image',
                required: true,
                icon: 'placeholder',
                classname:
                  'w-field w-field--model_choice_field w-field--admin_image_chooser',
              },
            ),
            new FieldBlockDefinition(
              'caption',
              new DummyWidgetDefinition('Caption widget'),
              {
                label: 'Caption',
                required: true,
                icon: 'placeholder',
                classname: 'w-field w-field--char_field w-field--text_input',
              },
            ),
          ],
          {
            label: 'Captioned image',
            required: false,
            icon: 'image',
            classname: 'captioned-image-block',
            helpText: 'image with a required <strong>caption</strong>',
            helpIcon: '<svg></svg>',
            collapsed: false,
            formLayout: new BlockGroupDefinition({
              children: [
                ['image', 'image'],
                ['caption', 'caption'],
              ],
              settings: [],
            }),
            ...nestedOpts,
          },
        ),
      ],
      {
        label: 'Hero',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'configure how the block is <strong>displayed</strong>',
        helpIcon: '<svg></svg>',
        collapsed: false,
        ...opts,
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', {
      text: 'Some highlighted text',
      url: 'https://example.com',
      accent_color: 'Test accent color',
      font_size: '16px',
      shown: true,
      captioned_image: {
        image: 'image-123',
        caption: 'An example image',
      },
    });
  };

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();
  });

  test('it renders correctly with flat children and settings', () => {
    setup({
      // group(root):
      //   children: [text, url, captioned_image]
      //   settings: [accent_color, font_size, shown]
      formLayout: new BlockGroupDefinition({
        children: [
          ['text', 'text'],
          ['url', 'url'],
          ['captioned_image', 'captioned_image'],
        ],
        settings: [
          ['accent_color', 'accent_color'],
          ['font_size', 'font_size'],
          ['shown', 'shown'],
        ],
      }),
    });

    expect(document.body.innerHTML).toMatchSnapshot();

    const button = document.querySelector(
      '[data-streamfield-action="SETTINGS"]',
    );
    expect(button).toBeTruthy();
    expect(button.getAttribute('aria-expanded')).toBe('false');
    const settings = document.querySelector('[data-block-settings]');
    expect(settings.hasAttribute('hidden')).toBe(true);

    // Check that the settings panel can be expanded by clicking the button
    button.click();
    expect(button.getAttribute('aria-expanded')).toBe('true');
    expect(settings.hasAttribute('hidden')).toBe(false);
  });

  test('it renders correctly with nested children and settings', () => {
    setup({
      // group(root):
      //   children:
      //     - group(main_content):
      //         children: [text]
      //         settings: [url]
      //     - captioned_image
      //   settings:
      //     - group(theme):
      //         children: [accent_color, font_size]
      //         settings: []
      //     - shown
      formLayout: new BlockGroupDefinition({
        children: [
          [
            new BlockGroupDefinition({
              children: [['text', 'text']],
              settings: [['url', 'url']],
              heading: 'Main content',
              classname: 'main-content',
              attrs: { 'data-example': 'value' },
              helpText: 'This is the <strong>main content</strong> area.',
              icon: 'doc-full',
            }),
            'main_content',
          ],
          ['captioned_image', 'captioned_image'],
        ],
        settings: [
          [
            new BlockGroupDefinition({
              children: [
                ['accent_color', 'accent_color'],
                ['font_size', 'font_size'],
              ],
              settings: [],
              heading: 'Theme',
              classname: 'theme-group collapsed',
              labelFormat: 'Color: {accent_color}, Size: {font_size}',
              icon: 'cogs',
            }),
            'theme',
          ],
          ['shown', 'shown'],
        ],
      }),
    });

    expect(document.body.innerHTML).toMatchSnapshot();

    const buttons = document.querySelectorAll(
      '[data-streamfield-action="SETTINGS"]',
    );
    expect(buttons.length).toBe(2);
    expect(
      [...buttons].every(
        (button) => button.getAttribute('aria-expanded') === 'false',
      ),
    ).toBe(true);
    const settings = document.querySelectorAll('[data-block-settings]');
    expect(settings.length).toBe(2);
    expect(
      [...settings].every((setting) => setting.hasAttribute('hidden')),
    ).toBe(true);

    // Check that the first settings panel can be expanded by clicking the button
    buttons[0].click();
    expect(buttons[0].getAttribute('aria-expanded')).toBe('true');
    expect(settings[0].hasAttribute('hidden')).toBe(false);

    // Shouldn't have affected the second settings panel
    expect(buttons[1].getAttribute('aria-expanded')).toBe('false');
    expect(settings[1].hasAttribute('hidden')).toBe(true);

    // Check that the second settings panel can be expanded by clicking the button
    buttons[1].click();
    expect(buttons[1].getAttribute('aria-expanded')).toBe('true');
    expect(settings[1].hasAttribute('hidden')).toBe(false);

    // The first settings panel should remain expanded
    expect(buttons[0].getAttribute('aria-expanded')).toBe('true');
    expect(settings[0].hasAttribute('hidden')).toBe(false);
  });

  test('it expands the parent group when the settings panel is expanded', () => {
    setup({
      // group(root):
      //   children:
      //     - group(main_content):
      //         children: [text]
      //         settings: [url]
      //     - captioned_image
      //   settings:
      //     - accent_color
      //     - font_size
      //     - shown
      formLayout: new BlockGroupDefinition({
        children: [
          [
            new BlockGroupDefinition({
              children: [['text', 'text']],
              settings: [['url', 'url']],
              heading: 'Main content',
              icon: 'doc-full',
            }),
            'main_content',
          ],
          ['captioned_image', 'captioned_image'],
        ],
        settings: [
          ['accent_color', 'accent_color'],
          ['font_size', 'font_size'],
          ['shown', 'shown'],
        ],
      }),
    });

    expect(document.body.innerHTML).toMatchSnapshot();

    // By default, the settings panel is collapsed
    const urlInput = document.querySelector('[data-contentpath="url"]');
    expect(urlInput).toBeTruthy();
    const settings = urlInput.closest('[data-block-settings]');
    expect(settings).toBeTruthy();
    expect(settings.hasAttribute('hidden')).toBe(true);
    const settingsButton = document.querySelector(
      `[aria-controls="${settings.id}"]`,
    );
    expect(settingsButton).toBeTruthy();
    expect(settingsButton.getAttribute('aria-expanded')).toBe('false');

    // It's within an expanded parent panel
    const panel = urlInput.closest('[data-panel]');
    expect(panel).toBeTruthy();
    const parentToggle = panel.querySelector('[data-panel-toggle]');
    expect(parentToggle).toBeTruthy();
    expect(parentToggle.getAttribute('aria-expanded')).toBe('true');
    const parentPanel = document.getElementById(
      parentToggle.getAttribute('aria-controls'),
    );
    expect(parentPanel).toBeTruthy();
    expect(parentPanel.hasAttribute('hidden')).toBe(false);

    // Expand the settings panel
    settingsButton.click();
    expect(settingsButton.getAttribute('aria-expanded')).toBe('true');
    expect(settings.hasAttribute('hidden')).toBe(false);

    // Try collapsing the parent panel
    parentToggle.click();
    expect(parentToggle.getAttribute('aria-expanded')).toBe('false');
    expect(parentPanel.hasAttribute('hidden')).toBe(true);

    // The settings panel should remain expanded
    // (but invisible because the parent is collapsed)
    expect(settingsButton.getAttribute('aria-expanded')).toBe('true');
    expect(settings.hasAttribute('hidden')).toBe(false);

    // Clicking the settings button should expand the parent panel, while the
    // settings panel should remain expanded instead of toggling to collapsed,
    // since the intention is to show the settings panel.
    settingsButton.click();
    expect(parentToggle.getAttribute('aria-expanded')).toBe('true');
    expect(parentPanel.hasAttribute('hidden')).toBe(false);
    expect(settingsButton.getAttribute('aria-expanded')).toBe('true');
    expect(settings.hasAttribute('hidden')).toBe(false);

    // Now try collapsing the settings panel
    settingsButton.click();
    expect(settingsButton.getAttribute('aria-expanded')).toBe('false');
    expect(settings.hasAttribute('hidden')).toBe(true);

    // The parent panel should remain expanded
    expect(parentToggle.getAttribute('aria-expanded')).toBe('true');
    expect(parentPanel.hasAttribute('hidden')).toBe(false);
  });

  test('it uses hidden="until-found" if the browser supports it', () => {
    // Mock support for hidden="until-found"
    document.body.onbeforematch = jest.fn();

    setup({
      // group(root):
      //   children:
      //     - group(main_content):
      //         children: [text]
      //         settings: [url]
      //     - captioned_image
      //   settings:
      //     - group(theme):
      //         children: [accent_color, font_size]
      //         settings: [shown]
      formLayout: new BlockGroupDefinition({
        children: [
          [
            new BlockGroupDefinition({
              children: [['text', 'text']],
              settings: [['url', 'url']],
              heading: 'Main content',
              classname: 'main-content',
              icon: 'doc-full',
            }),
            'main_content',
          ],
          ['captioned_image', 'captioned_image'],
        ],
        settings: [
          [
            new BlockGroupDefinition({
              children: [
                ['accent_color', 'accent_color'],
                ['font_size', 'font_size'],
              ],
              settings: [['shown', 'shown']],
              heading: 'Theme',
              classname: 'theme-group collapsed',
              icon: 'cogs',
            }),
            'theme',
          ],
        ],
      }),
    });

    const urlInput = document.querySelector('[data-contentpath="url"]');
    expect(urlInput).toBeTruthy();
    const mainSettings = urlInput.closest(
      '[data-block-settings][hidden="until-found"]',
    );
    expect(mainSettings).toBeTruthy();

    const shownInput = document.querySelector('[data-contentpath="shown"]');
    expect(shownInput).toBeTruthy();
    const nestedSettings = shownInput.closest(
      '[data-block-settings][hidden="until-found"]',
    );
    expect(nestedSettings).toBeTruthy();
    const themeSettings = nestedSettings.closest(
      '[data-block-settings][hidden="until-found"]',
    );
    expect(themeSettings).toBeTruthy();

    // Simulate finding the inputs using Ctrl+F, should expand any levels of
    // collapsible panels necessary to reveal the input.
    urlInput.dispatchEvent(new Event('beforematch', { bubbles: true }));
    expect(mainSettings.hasAttribute('hidden')).toBe(false);
    expect(urlInput.closest('[hidden]')).toBeNull();

    shownInput.dispatchEvent(new Event('beforematch', { bubbles: true }));
    expect(nestedSettings.hasAttribute('hidden')).toBe(false);
    expect(themeSettings.hasAttribute('hidden')).toBe(false);
    expect(shownInput.closest('[hidden]')).toBeNull();

    // Can toggle it back to hidden="until-found"
    const toggle = document.querySelector(
      `[aria-controls="${mainSettings.id}"]`,
    );
    expect(toggle).toBeTruthy();
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    toggle.click();
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(mainSettings.getAttribute('hidden')).toBe('until-found');

    delete document.body.onbeforematch;
  });

  test('it expands any level of nested panels to reveal errors', () => {
    setup({
      // group(root):
      //   children:
      //     - group(main_content):
      //         children: [text]
      //         settings: [url]
      //     - captioned_image
      //   settings:
      //     - group(theme):
      //         children: [accent_color, font_size]
      //         settings: [shown]
      formLayout: new BlockGroupDefinition({
        children: [
          [
            new BlockGroupDefinition({
              children: [['text', 'text']],
              settings: [['url', 'url']],
              heading: 'Main content',
              classname: 'main-content collapsed',
              icon: 'doc-full',
            }),
            'main_content',
          ],
          ['captioned_image', 'captioned_image'],
        ],
        settings: [
          [
            new BlockGroupDefinition({
              children: [
                ['accent_color', 'accent_color'],
                ['font_size', 'font_size'],
              ],
              settings: [['shown', 'shown']],
              heading: 'Theme',
              classname: 'theme-group collapsed',
              icon: 'cogs',
            }),
            'theme',
          ],
        ],
      }),
    });

    // Set errors on fields inside nested groups (this is normally done via the
    // parent StreamBlock, but we're testing the StructBlock directly here)
    boundBlock.setError({
      blockErrors: {
        text: { messages: ['This is not long enough.'] },
        shown: { messages: ['This must be checked.'] },
      },
    });

    expect(document.body.innerHTML).toMatchSnapshot();

    // Fields with errors are not descendants of a hidden element
    const textInput = document.querySelector('[data-contentpath="text"]');
    expect(textInput).toBeTruthy();
    expect(textInput.closest('[hidden]')).toBeNull();

    const shownInput = document.querySelector('[data-contentpath="shown"]');
    expect(shownInput).toBeTruthy();
    expect(shownInput.closest('[hidden]')).toBeNull();

    // Field without errors that is inside a collapsed panel remains hidden
    const urlInput = document.querySelector('[data-contentpath="url"]');
    expect(urlInput).toBeTruthy();
    const hidden = urlInput.closest('[hidden]');
    expect(hidden).toBeTruthy();
    expect(hidden.hasAttribute('data-block-settings')).toBe(true);
  });

  test('it supports custom formTemplate', () => {
    setup(
      {
        formTemplate: /* html */ `
          <div class="custom-form-template">
            <!--
              If the template iterates the child blocks using the 'children'
              context variable, it will follow the form_layout ordering.
              However, it's ultimately up to the template to decide the ordering
              of the child blocks, which can be different to form_layout e.g.
              when [data-structblock-child] is hardcoded in the template like this:
            -->
            <p>here comes the first field:</p>
            <div data-structblock-child="text"></div>
            <p>and here is a nested StructBlock that also has formTemplate and settings:</p>
            <div data-structblock-child="captioned_image"></div>
            <p>and here is another field block:</p>
            <div data-structblock-child="url"></div>

            <!--
              Must have an element with data-block-settings for toggling visibility,
              it can be placed anywhere in the template as long as it's not inside
              any data-structblock-child element.
            -->
            <div data-block-settings>
              <h3>Settings</h3>
              <div data-structblock-child="accent_color"></div>
              <div data-structblock-child="font_size"></div>
              <div data-structblock-child="shown"></div>
            </div>
          </div>
        `,
        // Nested BlockGroups are not allowed when using a custom formTemplate.
        // group(root):
        //   children: [text, url, captioned_image]
        //   settings: [accent_color, font_size, shown]
        formLayout: new BlockGroupDefinition({
          children: [
            ['url', 'url'],
            ['captioned_image', 'captioned_image'],
            ['text', 'text'],
          ],
          settings: [
            ['accent_color', 'accent_color'],
            ['font_size', 'font_size'],
            ['shown', 'shown'],
          ],
        }),
      },
      // Custom form template for the nested StructBlock
      {
        formTemplate: /* html */ `
          <div class="custom-child-structblock-form-template">
            <p>here comes the only block:</p>
            <div data-structblock-child="image"></div>

            <div data-block-settings>
              <h3>Captioned image settings</h3>
              <div data-structblock-child="caption"></div>
            </div>
          </div>
        `,
        formLayout: new BlockGroupDefinition({
          children: [['image', 'image']],
          settings: [['caption', 'caption']],
        }),
      },
    );

    expect(document.body.innerHTML).toMatchSnapshot();

    const buttons = document.querySelectorAll(
      '[data-streamfield-action="SETTINGS"]',
    );
    expect(buttons.length).toBe(2);
    expect(
      [...buttons].every(
        (btn) => btn.getAttribute('aria-expanded') === 'false',
      ),
    ).toBe(true);
    const settings = document.querySelectorAll('[data-block-settings]');
    expect(settings.length).toBe(2);
    expect([...settings].every((panel) => panel.hasAttribute('hidden'))).toBe(
      true,
    );

    // Check that the settings panels can be expanded by clicking the button
    buttons.forEach((button, index) => {
      button.click();
      expect(button.getAttribute('aria-expanded')).toBe('true');
      const panel = document.getElementById(
        button.getAttribute('aria-controls'),
      );
      expect(panel.hasAttribute('hidden')).toBe(false);
    });
  });
});

describe('telepath: wagtail.blocks.StructBlock in stream block', () => {
  let boundBlock;
  const setup = (formLayout) => {
    const defaultFormLayout = new BlockGroupDefinition({
      children: [
        ['inner_stream', 'inner_stream'],
        ['test_block_b', 'test_block_b'],
      ],
      settings: [],
    });
    // Setup test blocks - StreamBlock[StructBlock[StreamBlock[FieldBlock], FieldBlock]]
    const innerStreamDef = new StreamBlockDefinition(
      'inner_stream',
      [
        [
          '',
          [
            new FieldBlockDefinition(
              'test_block_a',
              new DummyWidgetDefinition('Block A Widget'),
              {
                label: 'Test Block A',
                required: false,
                icon: 'pilcrow',
                classname:
                  'w-field w-field--char_field w-field--admin_auto_height_text_input',
              },
            ),
          ],
        ],
      ],
      {},
      {
        label: 'Inner Stream',
        required: false,
        icon: 'placeholder',
        classname: null,
        helpText: '',
        helpIcon: '',
        maxNum: null,
        minNum: null,
        blockCounts: {},
      },
    );

    const structBlockDef = new StructBlockDefinition(
      'struct_block',
      [
        innerStreamDef,
        new FieldBlockDefinition(
          'test_block_b',
          new DummyWidgetDefinition('Block A Widget'),
          {
            label: 'Test Block B',
            required: false,
            icon: 'pilcrow',
            classname: '',
          },
        ),
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<svg></svg>',
        formLayout: formLayout || defaultFormLayout,
      },
    );

    const blockDef = new StreamBlockDefinition(
      '',
      [['', [structBlockDef]]],
      {},
      {
        label: '',
        required: true,
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>plenty</strong> of these',
        helpIcon: '<svg></svg>',
        maxNum: null,
        minNum: null,
        blockCounts: {},
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        type: 'struct_block',
        id: 'struct-block-1',
        value: {
          inner_stream: [
            { type: 'test_block_a', id: 'very-nested-1', value: 'foobar' },
          ],
          test_block_b: 'hello, world',
        },
      },
    ]);
  };

  test('ids are not duplicated when duplicating struct blocks', () => {
    setup();

    boundBlock.children[0].duplicate();

    const duplicatedStreamChild = boundBlock.children[1];
    const originalStreamChild = boundBlock.children[0];

    expect(duplicatedStreamChild).not.toHaveSameBlockIdAs(originalStreamChild);

    const duplicatedStreamBlockInStruct =
      duplicatedStreamChild.block.childBlocks.inner_stream;
    const originalStreamBlockInStruct =
      originalStreamChild.block.childBlocks.inner_stream;

    expect(duplicatedStreamBlockInStruct.children[0]).not.toHaveSameBlockIdAs(
      originalStreamBlockInStruct.children[0],
    );
  });

  test('using a custom formLayout with settings', () => {
    setup(
      // group(root):
      //   children: [inner_stream]
      //   settings: [test_block_b]
      new BlockGroupDefinition({
        children: [['inner_stream', 'inner_stream']],
        settings: [['test_block_b', 'test_block_b']],
      }),
    );

    // The settings button is rendered alongside other StreamBlock child controls
    expect(document.body.innerHTML).toMatchSnapshot();

    // Can duplicate the block including the settings without issues
    boundBlock.children[0].duplicate();
    const settingsButtons = document.querySelectorAll(
      '[data-streamfield-action="SETTINGS"]',
    );
    expect(settingsButtons.length).toBe(2);

    // Should have unique aria-controls attributes
    const originalSettingsPanelId =
      settingsButtons[0].getAttribute('aria-controls');
    const duplicatedSettingsPanelId =
      settingsButtons[1].getAttribute('aria-controls');
    expect(originalSettingsPanelId).not.toBe(duplicatedSettingsPanelId);

    // Should have unique IDs for the panels
    const settingsPanels = document.querySelectorAll('[data-block-settings]');
    expect(settingsPanels.length).toBe(2);
    expect(settingsPanels[0].id).toBe(originalSettingsPanelId);
    expect(settingsPanels[1].id).toBe(duplicatedSettingsPanelId);

    // Should have unique IDs for blocks
    const duplicatedStreamChild = boundBlock.children[1];
    const originalStreamChild = boundBlock.children[0];

    expect(duplicatedStreamChild).not.toHaveSameBlockIdAs(originalStreamChild);

    expect(originalStreamChild.block.childBlocks.test_block_b.idForLabel).toBe(
      'the-prefix-0-value-test_block_b',
    );
    expect(
      duplicatedStreamChild.block.childBlocks.test_block_b.idForLabel,
    ).toBe('the-prefix-1-value-test_block_b');
  });
});

describe('telepath: wagtail.blocks.StructBlock with formTemplate in stream block', () => {
  let boundBlock;

  beforeEach(() => {
    // Setup test blocks - StreamBlock[StructBlock[StreamBlock[FieldBlock], FieldBlock]]
    const innerStreamDef = new StreamBlockDefinition(
      'inner_stream',
      [
        [
          '',
          [
            new FieldBlockDefinition(
              'test_block_a',
              new DummyWidgetDefinition('Block A Widget'),
              {
                label: 'Test Block A',
                required: false,
                icon: 'pilcrow',
                classname:
                  'w-field w-field--char_field w-field--admin_auto_height_text_input',
              },
            ),
          ],
        ],
      ],
      {},
      {
        label: 'Inner Stream',
        required: false,
        icon: 'placeholder',
        classname: null,
        helpText: '',
        helpIcon: '',
        maxNum: null,
        minNum: null,
        blockCounts: {},
      },
    );

    const structBlockDef = new StructBlockDefinition(
      'struct_block',
      [
        innerStreamDef,
        new FieldBlockDefinition(
          'test_block_b',
          new DummyWidgetDefinition('Block A Widget'),
          {
            label: 'Test Block B',
            required: false,
            icon: 'pilcrow',
            classname: '',
          },
        ),
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<svg></svg>',
        formTemplate: `<div class="custom-form-template">
          <p>here comes the first field:</p>
          <div data-structblock-child="inner_stream"></div>
          <p>and here is the second:</p>
          <div data-structblock-child="test_block_b"></div>
        </div>`,
        formLayout: new BlockGroupDefinition({
          children: [
            ['inner_stream', 'inner_stream'],
            ['test_block_b', 'test_block_b'],
          ],
          settings: [],
        }),
      },
    );

    const blockDef = new StreamBlockDefinition(
      '',
      [['', [structBlockDef]]],
      {},
      {
        label: '',
        required: true,
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>plenty</strong> of these',
        helpIcon: '<svg></svg>',
        maxNum: null,
        minNum: null,
        blockCounts: {},
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        type: 'struct_block',
        id: 'struct-block-1',
        value: {
          inner_stream: [
            { type: 'test_block_a', id: 'very-nested-1', value: 'foobar' },
          ],
          test_block_b: 'hello, world',
        },
      },
    ]);
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});
