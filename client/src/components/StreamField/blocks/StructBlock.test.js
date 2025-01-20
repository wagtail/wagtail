import $ from 'jquery';
import { FieldBlockDefinition } from './FieldBlock';
import { StreamBlockDefinition } from './StreamBlock';
import { StructBlockDefinition } from './StructBlock';

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
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<svg></svg>',
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

describe('telepath: wagtail.blocks.StructBlock with formTemplate', () => {
  let boundBlock;
  let blockDefWithBadLabelFormat;

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
});

describe('telepath: wagtail.blocks.StructBlock in stream block', () => {
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
        strings: {
          MOVE_UP: 'Move up',
          MOVE_DOWN: 'Move down',
          DRAG: 'Drag',
          DELETE: 'Delete',
          DUPLICATE: 'Duplicate',
          ADD: 'Add',
        },
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
        strings: {
          MOVE_UP: 'Move up',
          MOVE_DOWN: 'Move down',
          DRAG: 'Drag',
          DELETE: 'Delete',
          DUPLICATE: 'Duplicate',
          ADD: 'Add',
        },
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

  test('ids are not duplicated when duplicating struct blocks', () => {
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
});
