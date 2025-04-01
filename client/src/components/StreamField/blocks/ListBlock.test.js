import $ from 'jquery';
import * as uuid from 'uuid';
import { FieldBlock, FieldBlockDefinition } from './FieldBlock';
import { ListBlockDefinition } from './ListBlock';
import { StreamBlockDefinition } from './StreamBlock';

// Mock uuid for consistent snapshot results
jest.mock('uuid');
const uuidSpy = jest.spyOn(uuid, 'v4');
uuidSpy.mockReturnValue('fake-uuid-v4-value');

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
      focus() {
        focus(widgetName);
      },
      idForLabel: id,
    };
  }
}

/* ListBlock should not call setError on its children with a null value; FieldBlock handles this
gracefully, so define a custom one that doesn't
*/

class ParanoidFieldBlock extends FieldBlock {
  setError(errorList) {
    if (!errorList) {
      throw new Error(
        'ParanoidFieldBlock.setError was passed a null errorList',
      );
    }
    return super.setError(errorList);
  }
}

class ParanoidFieldBlockDefinition extends FieldBlockDefinition {
  render(placeholder, prefix, initialState, initialError, capabilities) {
    return new ParanoidFieldBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
      capabilities,
    );
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
      new ParanoidFieldBlockDefinition(
        '',
        new DummyWidgetDefinition('The widget'),
        {
          label: '',
          required: true,
          icon: 'pilcrow',
          classname:
            'w-field w-field--char_field w-field--admin_auto_height_text_input',
        },
      ),
      null,
      {
        label: 'Test listblock',
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>a few</strong> of these',
        helpIcon: '<svg></svg>',
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
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
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
      'value: The widget - the-prefix-1-value',
    ]);
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual([
      {
        value: 'state: The widget - the-prefix-0-value',
        id: '11111111-1111-1111-1111-111111111111',
      },
      {
        value: 'state: The widget - the-prefix-1-value',
        id: '22222222-2222-2222-2222-222222222222',
      },
    ]);
  });

  test('setState() creates new widgets', () => {
    boundBlock.setState([
      {
        value: 'Changed first value',
        id: '11111111-1111-1111-1111-111111111111',
      },
      {
        value: 'Changed second value',
        id: '22222222-2222-2222-2222-222222222222',
      },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
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
      {
        value: 'state: The widget - the-prefix-0-value',
        id: '11111111-1111-1111-1111-111111111111',
      },
      {
        value: 'state: The widget - the-prefix-1-value',
        id: '22222222-2222-2222-2222-222222222222',
      },
      {
        value: 'state: The widget - the-prefix-2-value',
        id: '33333333-3333-3333-3333-333333333333',
      },
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

  test('duplicated blocks have unique ids', () => {
    boundBlock.duplicateBlock(0);

    expect(boundBlock.children[1]).not.toHaveSameBlockIdAs(
      boundBlock.children[0],
    );
  });

  test('blocks can be split', () => {
    boundBlock.splitBlock(0, 'first', 'value');

    expect(setState.mock.calls.length).toBe(1);
    expect(constructor.mock.calls[0][0]).toBe('The widget');
    expect(setState.mock.calls[0][1]).toBe('first');

    expect(constructor.mock.calls.length).toBe(3);

    expect(constructor.mock.calls[2][0]).toBe('The widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      initialState: 'value',
    });

    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('setError passes error messages to children', () => {
    boundBlock.setError({
      blockErrors: { 1: { messages: ['Not as good as the first one.'] } },
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('setError renders non-block errors', () => {
    boundBlock.setError({
      messages: ['At least three blocks are required'],
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.ListBlock with maxNum set', () => {
  // Define a test block
  const blockDef = new ListBlockDefinition(
    'test_listblock',
    new ParanoidFieldBlockDefinition(
      '',
      new DummyWidgetDefinition('The widget'),
      {
        label: '',
        required: true,
        icon: 'pilcrow',
        classname:
          'w-field w-field--char_field w-field--admin_auto_height_text_input',
      },
    ),
    null,
    {
      label: 'Test listblock',
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>a few</strong> of these',
      helpIcon: '<svg></svg>',
      maxNum: 3,
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

  const assertCanAddBlock = () => {
    // Test duplicate button
    // querySelector always returns the first element it sees so this only checks the first block
    expect(
      document
        .querySelector('button[title="Duplicate"]')
        .getAttribute('disabled'),
    ).toBe(null);

    // Test menu
    expect(
      document
        .querySelector('button[data-streamfield-list-add]')
        .getAttribute('disabled'),
    ).toBe(null);
  };

  const assertShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical').innerHTML).toBe(
      'The maximum number of items is 3',
    );
  };

  const assertNotShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical')).toBe(null);
  };

  test('test error message not show when at limit', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
    ]);

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });

  test('initialising at over maxNum shows error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
      { value: 'Fourth value', id: '44444444-4444-4444-4444-444444444444' },
    ]);

    assertCanAddBlock();
    assertShowingErrorMessage();
  });

  test('addSibling capability works', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
    ]);
    const addSibling =
      boundBlock.children[0].block.parentCapabilities.get('addSibling');
    expect(addSibling.getBlockMax()).toEqual(3);
    expect(addSibling.getBlockCount()).toEqual(3);
    addSibling.fn();
    expect(boundBlock.children.length).toEqual(4);
  });

  test('insert adds error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
    ]);

    assertCanAddBlock();
    assertNotShowingErrorMessage();

    boundBlock.insert('Fourth value', 2);

    assertCanAddBlock();
    assertShowingErrorMessage();
  });

  test('delete removes error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
      { value: 'Third value', id: '33333333-3333-3333-3333-333333333333' },
      { value: 'Fourth value', id: '44444444-4444-4444-4444-444444444444' },
    ]);

    assertCanAddBlock();
    assertShowingErrorMessage();

    boundBlock.deleteBlock(2);

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.ListBlock with minNum set', () => {
  // Define a test block
  const blockDef = new ListBlockDefinition(
    'test_listblock',
    new ParanoidFieldBlockDefinition(
      '',
      new DummyWidgetDefinition('The widget'),
      {
        label: '',
        required: true,
        icon: 'pilcrow',
        classname:
          'w-field w-field--char_field w-field--admin_auto_height_text_input',
      },
    ),
    null,
    {
      label: 'Test listblock',
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>a few</strong> of these',
      helpIcon: '<svg></svg>',
      minNum: 2,
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

  const assertShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical').innerHTML).toBe(
      'The minimum number of items is 2',
    );
  };

  const assertNotShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical')).toBe(null);
  };

  test('test error message not shown when at limit', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
    ]);

    assertNotShowingErrorMessage();
  });

  test('initialising at under minNum shows error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
    ]);

    assertShowingErrorMessage();
  });

  test('insert removes error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
    ]);

    assertShowingErrorMessage();

    boundBlock.insert('Second value', 1);

    assertNotShowingErrorMessage();
  });

  test('delete below limit adds error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      { value: 'First value', id: '11111111-1111-1111-1111-111111111111' },
      { value: 'Second value', id: '22222222-2222-2222-2222-222222222222' },
    ]);

    assertNotShowingErrorMessage();

    boundBlock.deleteBlock(1);

    assertShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.ListBlock with StreamBlock child', () => {
  let boundBlock;

  beforeEach(() => {
    // Define test blocks - ListBlock[StreamBlock[FieldBlock]]
    const blockDef = new ListBlockDefinition(
      'list',
      new StreamBlockDefinition(
        '',
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
      ),
      null,
      {
        label: 'Test listblock',
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>a few</strong> of these',
        helpIcon: '<svg></svg>',
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
        id: 'stream-block-1',
        value: [
          {
            type: 'test_block_a',
            value: 'hello',
            id: 'inner-block-1',
          },
        ],
      },
    ]);
  });

  test('ids in nested stream blocks are not duplicated', () => {
    // Duplicate the outermost stream block list item
    boundBlock.duplicateBlock(0);

    const duplicatedStreamBlock = boundBlock.children[1].block;
    const originalStreamBlock = boundBlock.children[0].block;

    // Test the ids on the duplicated stream child of the stream-block-in-list-block
    expect(duplicatedStreamBlock.children[0]).not.toHaveSameBlockIdAs(
      originalStreamBlock.children[0],
    );
  });
});

describe('telepath: wagtail.blocks.ListBlock inside a StreamBlock', () => {
  let boundBlock;

  beforeEach(() => {
    // Create test blocks - StreamBlock[ListBlock[FieldBlock]]
    const listBlockDef = new ListBlockDefinition(
      'list',
      new ParanoidFieldBlockDefinition(
        '',
        new DummyWidgetDefinition('The widget'),
        {
          label: '',
          required: true,
          icon: 'pilcrow',
          classname:
            'w-field w-field--char_field w-field--admin_auto_height_text_input',
        },
      ),
      null,
      {
        label: 'Test listblock',
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>a few</strong> of these',
        helpIcon: '<svg></svg>',
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

    const blockDef = new StreamBlockDefinition(
      '',
      [['', [listBlockDef]]],
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
        type: 'list',
        id: 'list-1',
        value: [{ id: 'list-item-1', value: 'foobar' }],
      },
    ]);
  });

  test('ids of list blocks in a stream block are not duplicated', () => {
    boundBlock.duplicateBlock(0);
    const originalStreamChild = boundBlock.children[0];
    const duplicatedStreamChild = boundBlock.children[1];

    expect(duplicatedStreamChild).not.toHaveSameBlockIdAs(originalStreamChild);

    expect(duplicatedStreamChild.block.children[0]).not.toHaveSameBlockIdAs(
      originalStreamChild.block.children[0],
    );
  });
});
