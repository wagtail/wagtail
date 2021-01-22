/* eslint-disable no-unused-vars */
import './telepath';
import './blocks';

import $ from 'jquery';
window.$ = $;

// Define some callbacks in global scope that can be mocked in tests
let constructor = (_widgetName, _name, _id, _initialState) => {};
let setState = (_widgetName, _state) => {};
let getState = (_widgetName) => {};
let getValue = (_widgetName) => {};
let focus = (_widgetName) => {};

class DummyWidget {
  constructor(widgetName) {
    this.widgetName = widgetName;
  }

  render(placeholder, name, id, initialState) {
    const widgetName = this.widgetName;
    constructor(widgetName, { name, id, initialState });

    $(placeholder).replaceWith(`<p name="${name}" id="${id}">${widgetName}</p>`);
    return {
      setState(state) { setState(widgetName, state); },
      getState() { getState(widgetName); return `state: ${widgetName} - ${name}`; },
      getValue() { getValue(widgetName); return `value: ${widgetName} - ${name}`; },
      focus() { focus(widgetName); },
      idForLabel: id,
    };
  }
}
window.telepath.register('wagtail.widgets.DummyWidget', DummyWidget);

describe('telepath: wagtail.blocks.FieldBlock', () => {
  let boundField;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Create a placeholder to render the block
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render
    const fieldDef = window.telepath.unpack({
      _type: 'wagtail.blocks.FieldBlock',
      _args: ['test_field', {
        _type: 'wagtail.widgets.DummyWidget',
        _args: ['The widget']
      }, {
        label: 'Test Field',
        required: true,
        icon: 'placeholder',
        classname: 'field char_field widget-text_input fieldname-test_charblock',
        helpText: 'drink <em>more</em> water'
      }]
    });
    boundField = fieldDef.render($('#placeholder'), 'the-prefix', 'Test initial state');
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('constructor is called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(1);
    expect(constructor.mock.calls[0][0]).toBe('The widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix',
      id: 'the-prefix',
      initialState: 'Test initial state',
    });
  });

  test('getValue() calls widget getValue()', () => {
    const value = boundField.getValue();
    expect(getValue.mock.calls.length).toBe(1);
    expect(value).toEqual('value: The widget - the-prefix');
  });

  test('getState() calls widget getState()', () => {
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(1);
    expect(state).toEqual('state: The widget - the-prefix');
  });

  test('setState() calls widget setState()', () => {
    boundField.setState('Test changed state');
    expect(setState.mock.calls.length).toBe(1);
    expect(setState.mock.calls[0][0]).toBe('The widget');
    expect(setState.mock.calls[0][1]).toBe('Test changed state');
  });

  test('focus() calls widget focus()', () => {
    boundField.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('The widget');
  });
});

describe('telepath: wagtail.blocks.StructBlock', () => {
  let boundField;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Create a placeholder to render the block
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render
    const fieldDef = window.telepath.unpack({
      _type: 'wagtail.blocks.StructBlock',
      _args: ['heading_block', [{
        _type: 'wagtail.blocks.FieldBlock',
        _args: ['heading_text', {
          _type: 'wagtail.widgets.DummyWidget',
          _args: ['Heading widget']
        }, {
          label: 'Heading text',
          required: true,
          icon: 'placeholder',
          classname: 'field char_field widget-text_input fieldname-heading_text'
        }]
      }, {
        _type: 'wagtail.blocks.FieldBlock',
        _args: ['size', {
          _type: 'wagtail.widgets.DummyWidget',
          _args: ['Size widget']
        }, {
          label: 'Size',
          required: false,
          icon: 'placeholder',
          classname: 'field choice_field widget-select fieldname-size'
        }]
      }], {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<div class="icon-help">?</div>',
      }]
    });
    boundField = fieldDef.render($('#placeholder'), 'the-prefix', {
      heading_text: 'Test heading text',
      size: '123'
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
    const value = boundField.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual({
      heading_text: 'value: Heading widget - the-prefix-heading_text',
      size: 'value: Size widget - the-prefix-size'
    });
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual({
      heading_text: 'state: Heading widget - the-prefix-heading_text',
      size: 'state: Size widget - the-prefix-size'
    });
  });

  test('setState() calls setState() on all widgets', () => {
    boundField.setState({
      heading_text: 'Changed heading text',
      size: '456'
    });
    expect(setState.mock.calls.length).toBe(2);
    expect(setState.mock.calls[0][0]).toBe('Heading widget');
    expect(setState.mock.calls[0][1]).toBe('Changed heading text');
    expect(setState.mock.calls[1][0]).toBe('Size widget');
    expect(setState.mock.calls[1][1]).toBe('456');
  });

  test('focus() calls focus() on first widget', () => {
    boundField.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Heading widget');
  });
});

describe('telepath: wagtail.blocks.ListBlock', () => {
  let boundField;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Create a placeholder to render the block
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render
    const fieldDef = window.telepath.unpack({
      _type: 'wagtail.blocks.ListBlock',
      _args: ['test_listblock', {
        _type: 'wagtail.blocks.FieldBlock',
        _args: ['', {
          _type: 'wagtail.widgets.DummyWidget',
          _args: ['The widget']
        }, {
          label: '',
          required: true,
          icon: 'pilcrow',
          classname: 'field char_field widget-admin_auto_height_text_input fieldname-'
        }]
      }, null, {
        label: 'Test listblock',
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>a few</strong> of these',
        helpIcon: '<div class="icon-help">?</div>',
      }]
    });
    boundField = fieldDef.render($('#placeholder'), 'the-prefix', [
      'First value',
      'Second value'
    ]);
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(2);

    expect(constructor.mock.calls[0][0]).toBe('The widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-0-value',
      id: 'the-prefix-0-value',
      initialState: 'First value',
    });

    expect(constructor.mock.calls[1][0]).toBe('The widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-1-value',
      id: 'the-prefix-1-value',
      initialState: 'Second value',
    });
  });

  test('getValue() calls getValue() on widget for both values', () => {
    const value = boundField.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual([
      'value: The widget - the-prefix-0-value',
      'value: The widget - the-prefix-1-value'
    ]);
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual([
      'state: The widget - the-prefix-0-value',
      'state: The widget - the-prefix-1-value'
    ]);
  });

  test('setState() creates new widgets', () => {
    boundField.setState([
      'Changed first value',
      'Changed second value',
      'Third value'
    ]);

    // Includes the two initial calls, plus the three new ones
    expect(constructor.mock.calls.length).toBe(5);

    expect(constructor.mock.calls[2][0]).toBe('The widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-0-value',
      id: 'the-prefix-0-value',
      initialState: 'Changed first value',
    });

    expect(constructor.mock.calls[3][0]).toBe('The widget');
    expect(constructor.mock.calls[3][1]).toEqual({
      name: 'the-prefix-1-value',
      id: 'the-prefix-1-value',
      initialState: 'Changed second value',
    });

    expect(constructor.mock.calls[4][0]).toBe('The widget');
    expect(constructor.mock.calls[4][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      initialState: 'Third value',
    });

    // Let's get the state now to make sure the initial widgets are gone
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(3);
    expect(state).toEqual([
      'state: The widget - the-prefix-0-value',
      'state: The widget - the-prefix-1-value',
      'state: The widget - the-prefix-2-value'
    ]);
  });

  test('focus() calls focus() on first widget', () => {
    boundField.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('The widget');
  });
});

describe('telepath: wagtail.blocks.StreamBlock', () => {
  let boundField;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Create a placeholder to render the block
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render
    const fieldDef = window.telepath.unpack({
      _type: 'wagtail.blocks.StreamBlock',
      _args: ['', [['', [{
        _type: 'wagtail.blocks.FieldBlock',
        _args: ['test_block_a', {
          _type: 'wagtail.widgets.DummyWidget',
          _args: ['Block A widget']
        }, {
          label: 'Test Block B',
          required: true,
          icon: 'placeholder',
          classname: 'field char_field widget-text_input fieldname-test_charblock'
        }]
      }, {
        _type: 'wagtail.blocks.FieldBlock',
        _args: ['test_block_b', {
          _type: 'wagtail.widgets.DummyWidget',
          _args: ['Block B widget']
        }, {
          label: 'Test Block B',
          required: true,
          icon: 'pilcrow',
          classname: 'field char_field widget-admin_auto_height_text_input fieldname-test_textblock'
        }]
      }
      ]]], {
        test_block_a: 'Block A options',
        test_block_b: 'Block B options',
      }, {
        label: '',
        required: true,
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>plenty</strong> of these',
        helpIcon: '<div class="icon-help">?</div>',
        maxNum: null,
        minNum: null,
        blockCounts: {}
      }]
    });
    boundField = fieldDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value'
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value'
      },
    ]);
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('Widget constructors are called with correct parameters', () => {
    expect(constructor.mock.calls.length).toBe(2);

    expect(constructor.mock.calls[0][0]).toBe('Block A widget');
    expect(constructor.mock.calls[0][1]).toEqual({
      name: 'the-prefix-0-value',
      id: 'the-prefix-0-value',
      initialState: 'First value',
    });

    expect(constructor.mock.calls[1][0]).toBe('Block B widget');
    expect(constructor.mock.calls[1][1]).toEqual({
      name: 'the-prefix-1-value',
      id: 'the-prefix-1-value',
      initialState: 'Second value',
    });
  });

  test('getValue() calls getValue() on widget for both values', () => {
    const value = boundField.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'value: Block A widget - the-prefix-0-value'
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'value: Block B widget - the-prefix-1-value'
      },
    ]);
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'state: Block A widget - the-prefix-0-value'
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-1-value'
      },
    ]);
  });

  test('setState() creates new widgets', () => {
    boundField.setState([
      {
        id: '1',
        type: 'test_block_a',
        value: 'Changed first value'
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value'
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Changed second value'
      },
    ]);

    // Includes the two initial calls, plus the three new ones
    expect(constructor.mock.calls.length).toBe(5);

    expect(constructor.mock.calls[2][0]).toBe('Block A widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-0-value',
      id: 'the-prefix-0-value',
      initialState: 'Changed first value',
    });

    expect(constructor.mock.calls[3][0]).toBe('Block B widget');
    expect(constructor.mock.calls[3][1]).toEqual({
      name: 'the-prefix-1-value',
      id: 'the-prefix-1-value',
      initialState: 'Third value',
    });

    expect(constructor.mock.calls[4][0]).toBe('Block B widget');
    expect(constructor.mock.calls[4][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      initialState: 'Changed second value',
    });

    // Let's get the state now to make sure the initial widgets are gone
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(3);
    expect(state).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'state: Block A widget - the-prefix-0-value'
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-1-value'
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-2-value'
      },
    ]);
  });

  test('focus() calls focus() on first widget', () => {
    boundField.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Block A widget');
  });
});
