/* eslint-disable @typescript-eslint/no-unused-vars */

import { FieldBlockDefinition } from './FieldBlock';
import { ListBlockDefinition } from './ListBlock';

import $ from 'jquery';
window.$ = $;

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

describe('telepath: wagtail.blocks.ListBlock', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new ListBlockDefinition(
      'test_listblock',
      new FieldBlockDefinition(
        '',
        new DummyWidgetDefinition('The widget'),
        {
          label: '',
          required: true,
          icon: 'pilcrow',
          classname: 'field char_field widget-admin_auto_height_text_input fieldname-'
        }
      ),
      null,
      {
        label: 'Test listblock',
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>a few</strong> of these',
        helpIcon: '<div class="icon-help">?</div>',
        strings: {
          MOVE_UP: 'Move up',
          MOVE_DOWN: 'Move down',
          DELETE: 'Delete',
          DUPLICATE: 'Duplicate',
          ADD: 'Add',
        },
      }
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
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
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual([
      'value: The widget - the-prefix-0-value',
      'value: The widget - the-prefix-1-value'
    ]);
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual([
      'state: The widget - the-prefix-0-value',
      'state: The widget - the-prefix-1-value'
    ]);
  });

  test('setState() creates new widgets', () => {
    boundBlock.setState([
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
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(3);
    expect(state).toEqual([
      'state: The widget - the-prefix-0-value',
      'state: The widget - the-prefix-1-value',
      'state: The widget - the-prefix-2-value'
    ]);
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('The widget');
  });

  test('deleteBlock() deletes a block', () => {
    boundBlock.deleteBlock(1);
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('blocks can be reordered upward', () => {
    boundBlock.moveBlock(1, 0);
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('blocks can be reordered downward', () => {
    boundBlock.moveBlock(0, 1);
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('blocks can be duplicated', () => {
    boundBlock.duplicateBlock(1);
    expect(constructor.mock.calls.length).toBe(3);

    expect(constructor.mock.calls[2][0]).toBe('The widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      // new block gets state from the one being duplicated
      initialState: 'state: The widget - the-prefix-1-value',
    });

    expect(document.body.innerHTML).toMatchSnapshot();
  });
});
