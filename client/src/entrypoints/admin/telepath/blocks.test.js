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
      getState() { getState(widgetName); return `state: ${widgetName}`; },
      getValue() { getValue(widgetName); return `value: ${widgetName}`; },
      focus() { focus(widgetName); },
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
        classname: 'field char_field widget-text_input fieldname-test_charblock'
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
    expect(value).toEqual('value: The widget');
  });

  test('getState() calls widget getState()', () => {
    const state = boundField.getState();
    expect(getState.mock.calls.length).toBe(1);
    expect(state).toEqual('state: The widget');
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
