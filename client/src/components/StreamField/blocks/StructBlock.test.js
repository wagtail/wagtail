import $ from 'jquery';
import { FieldBlockDefinition } from './FieldBlock';
import {
  StructBlockDefinition,
  StructBlockValidationError,
} from './StructBlock';

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

class ValidationError {
  constructor(messages) {
    this.messages = messages;
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
            classname:
              'field char_field widget-text_input fieldname-heading_text',
          },
        ),
        new FieldBlockDefinition(
          'size',
          new DummyWidgetDefinition('Size widget'),
          {
            label: 'Size',
            required: false,
            icon: 'placeholder',
            classname: 'field choice_field widget-select fieldname-size',
          },
        ),
      ],
      {
        label: 'Heading block',
        required: false,
        icon: 'title',
        classname: 'struct-block',
        helpText: 'use <strong>lots</strong> of these',
        helpIcon: '<div class="icon-help">?</div>',
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
    boundBlock.setError([
      new StructBlockValidationError({
        size: [new ValidationError(['This is too big'])],
      }),
    ]);
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StructBlock with formTemplate', () => {
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
            classname:
              'field char_field widget-text_input fieldname-heading_text',
          },
        ),
        new FieldBlockDefinition(
          'size',
          new DummyWidgetDefinition('Size widget'),
          {
            label: 'Size',
            required: false,
            icon: 'placeholder',
            classname: 'field choice_field widget-select fieldname-size',
          },
        ),
      ],
      {
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

  test('getTextLabel() returns text label according to labelFormat', () => {
    expect(boundBlock.getTextLabel()).toBe(
      'label: the-prefix-heading_text - label: the-prefix-size',
    );
  });
});
