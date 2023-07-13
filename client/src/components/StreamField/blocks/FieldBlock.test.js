import $ from 'jquery';
import { FieldBlockDefinition } from './FieldBlock';

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
  constructor(widgetName, { throwErrorOnRender = false } = {}) {
    this.widgetName = widgetName;
    this.throwErrorOnRender = throwErrorOnRender;
  }

  render(placeholder, name, id, initialState) {
    if (this.throwErrorOnRender) {
      throw new Error('Mock rendering error');
    }

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
      focus() {
        focus(widgetName);
      },
      idForLabel: id,
    };
  }
}

describe('telepath: wagtail.blocks.FieldBlock', () => {
  let boundBlock;

  window.comments = {
    initAddCommentButton: jest.fn(),
    getContentPath: jest.fn(),
  };

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new FieldBlockDefinition(
      'test_field',
      new DummyWidgetDefinition('The widget'),
      {
        label: 'Test Field',
        required: true,
        icon: 'placeholder',
        classname: 'w-field w-field--char_field w-field--text_input',
        helpText: 'drink <em>more</em> water',
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render(
      $('#placeholder'),
      'the-prefix',
      'Test initial state',
    );
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
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(1);
    expect(value).toEqual('value: The widget - the-prefix');
  });

  test('getState() calls widget getState()', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(1);
    expect(state).toEqual('state: The widget - the-prefix');
  });

  test('setState() calls widget setState()', () => {
    boundBlock.setState('Test changed state');
    expect(setState.mock.calls.length).toBe(1);
    expect(setState.mock.calls[0][0]).toBe('The widget');
    expect(setState.mock.calls[0][1]).toBe('Test changed state');
  });

  test('focus() calls widget focus()', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('The widget');
  });

  test('setError() renders errors', () => {
    boundBlock.setError({
      messages: [
        'Field must not contain the letter E',
        'Field must contain a story about kittens',
      ],
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.FieldBlock with comments enabled', () => {
  let boundBlock;

  window.comments = {
    initAddCommentButton: jest.fn(),
    getContentPath: jest.fn(),
  };

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new FieldBlockDefinition(
      'test_field',
      new DummyWidgetDefinition('The widget'),
      {
        label: 'Test Field',
        required: true,
        icon: 'placeholder',
        classname: 'w-field w-field--char_field w-field--text_input',
        helpText: 'drink <em>more</em> water',
        showAddCommentButton: true,
        strings: {
          ADD_COMMENT: 'Add Comment',
        },
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render(
      $('#placeholder'),
      'the-prefix',
      'Test initial state',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.FieldBlock catches widget render errors', () => {
  let boundBlock;

  beforeEach(() => {
    // mock console.error to ensure it does not bubble to the logs
    jest.spyOn(console, 'error').mockImplementation(() => {});

    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new FieldBlockDefinition(
      'test_field',
      new DummyWidgetDefinition('The widget', { throwErrorOnRender: true }),
      {
        label: 'Test Field',
        required: true,
        icon: 'placeholder',
        classname: 'w-field w-field--char_field w-field--text_input',
        helpText: 'drink <em>more</em> water',
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';

    boundBlock = blockDef.render(
      $('#placeholder'),
      'the-prefix',
      'Test initial state',
    );
  });

  afterEach(() => {
    /* eslint-disable no-console */
    console.error.mockRestore();
  });

  test('it renders correctly', () => {
    expect(console.error).toHaveBeenCalledTimes(1);
    expect(console.error).toHaveBeenCalledWith(
      new Error('Mock rendering error'),
    );
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});
