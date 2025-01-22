import $ from 'jquery';
import * as uuid from 'uuid';
import { FieldBlockDefinition } from './FieldBlock';
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

describe('telepath: wagtail.blocks.StreamBlock', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new StreamBlockDefinition(
      '',
      [
        [
          '',
          [
            new FieldBlockDefinition(
              'test_block_a',
              new DummyWidgetDefinition('Block A widget'),
              {
                label: 'Test Block A',
                required: true,
                icon: 'placeholder',
                classname: 'w-field w-field--char_field w-field--text_input',
              },
            ),
            new FieldBlockDefinition(
              'test_block_b',
              new DummyWidgetDefinition('Block B widget'),
              {
                label: 'Test Block B',
                required: true,
                icon: 'pilcrow',
                classname:
                  'w-field w-field--char_field w-field--admin_auto_height_text_input',
              },
            ),
          ],
        ],
      ],
      {
        test_block_a: 'Block A options',
        test_block_b: 'Block B options',
      },
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
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('it renders menus on opening', () => {
    boundBlock.inserters[1].open();
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
    const value = boundBlock.getValue();
    expect(getValue.mock.calls.length).toBe(2);
    expect(value).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'value: Block A widget - the-prefix-0-value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'value: Block B widget - the-prefix-1-value',
      },
    ]);
  });

  test('getState() calls getState() on all widgets', () => {
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(2);
    expect(state).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'state: Block A widget - the-prefix-0-value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-1-value',
      },
    ]);
  });

  test('setState() creates new widgets', () => {
    boundBlock.setState([
      {
        id: '1',
        type: 'test_block_a',
        value: 'Changed first value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Changed second value',
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
    const state = boundBlock.getState();
    expect(getState.mock.calls.length).toBe(3);
    expect(state).toEqual([
      {
        id: '1',
        type: 'test_block_a',
        value: 'state: Block A widget - the-prefix-0-value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-1-value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'state: Block B widget - the-prefix-2-value',
      },
    ]);
  });

  test('focus() calls focus() on first widget', () => {
    boundBlock.focus();
    expect(focus.mock.calls.length).toBe(1);
    expect(focus.mock.calls[0][0]).toBe('Block A widget');
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

    expect(constructor.mock.calls[2][0]).toBe('Block B widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      // new block gets state from the one being duplicated
      initialState: 'state: Block B widget - the-prefix-1-value',
    });

    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('blocks can be split', () => {
    boundBlock.splitBlock(0, 'first', 'value');

    expect(setState.mock.calls.length).toBe(1);
    expect(constructor.mock.calls[0][0]).toBe('Block A widget');
    expect(setState.mock.calls[0][1]).toBe('first');

    expect(constructor.mock.calls.length).toBe(3);

    expect(constructor.mock.calls[2][0]).toBe('Block A widget');
    expect(constructor.mock.calls[2][1]).toEqual({
      name: 'the-prefix-2-value',
      id: 'the-prefix-2-value',
      initialState: 'value',
    });
  });

  test('setError renders error messages', () => {
    boundBlock.setError({
      messages: [
        /* non-block error */
        'At least three blocks are required',
      ],
      blockErrors: {
        /* block error */
        1: { messages: ['Not as good as the first one.'] },
      },
    });
    expect(document.body.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with nested stream block', () => {
  let boundBlock;

  beforeEach(() => {
    // Define a test block - StreamBlock[StreamBlock[FieldBlock]]
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

    const blockDef = new StreamBlockDefinition(
      '',
      [['', [innerStreamDef]]],
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
        type: 'inner_stream',
        value: [{ type: 'test_block_a', value: 'hello', id: 'inner-block-1' }],
        id: 'nested-stream-1',
      },
    ]);
  });

  test('duplicateBlock does not duplicate block ids', () => {
    boundBlock.children[0].duplicate();
    const duplicatedStreamChild = boundBlock.children[1];
    const originalStreamChild = boundBlock.children[0];

    // Test the outermost stream child
    expect(duplicatedStreamChild).not.toHaveSameBlockIdAs(originalStreamChild);

    // Test the nested child
    expect(duplicatedStreamChild.block.children[0]).not.toHaveSameBlockIdAs(
      originalStreamChild.block.children[0],
    );
  });
});

describe('telepath: wagtail.blocks.StreamBlock with labels that need escaping', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new StreamBlockDefinition(
      '',
      [
        [
          '',
          [
            new FieldBlockDefinition(
              'test_block_a',
              new DummyWidgetDefinition('Block A widget'),
              {
                label: 'Test Block <A>',
                required: true,
                icon: 'placeholder',
                classname: 'w-field w-field--char_field w-field--text_input',
              },
            ),
            new FieldBlockDefinition(
              'test_block_b',
              new DummyWidgetDefinition('Block B widget'),
              {
                label: 'Test Block <B>',
                required: true,
                icon: 'pilcrow',
                classname:
                  'w-field w-field--char_field w-field--admin_auto_height_text_input',
              },
            ),
          ],
        ],
      ],
      {
        test_block_a: 'Block A options',
        test_block_b: 'Block B options',
      },
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
          DELETE: 'Delete & kill with fire',
          DUPLICATE: 'Duplicate',
          ADD: 'Add',
        },
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
  });

  test('it renders correctly', () => {
    boundBlock.inserters[0].open();
    const listbox = document.querySelector('[role="listbox"]');
    expect(listbox.innerHTML).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with maxNum set', () => {
  // Define a test block
  const blockDef = new StreamBlockDefinition(
    '',
    [
      [
        '',
        [
          new FieldBlockDefinition(
            'test_block_a',
            new DummyWidgetDefinition('Block A widget'),
            {
              label: 'Test Block <A>',
              required: true,
              icon: 'placeholder',
              classname: 'w-field w-field--char_field w-field--text_input',
            },
          ),
          new FieldBlockDefinition(
            'test_block_b',
            new DummyWidgetDefinition('Block B widget'),
            {
              label: 'Test Block <B>',
              required: true,
              icon: 'pilcrow',
              classname:
                'w-field w-field--char_field w-field--admin_auto_height_text_input',
            },
          ),
        ],
      ],
    ],
    {
      test_block_a: 'Block A options',
      test_block_b: 'Block B options',
    },
    {
      label: '',
      required: true,
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>plenty</strong> of these',
      helpIcon: '<svg></svg>',
      maxNum: 3,
      minNum: null,
      blockCounts: {},
      strings: {
        MOVE_UP: 'Move up',
        MOVE_DOWN: 'Move down',
        DRAG: 'Drag',
        DELETE: 'Delete & kill with fire',
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
        .querySelector('button[title="Insert a block"]')
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

  test('test no error message when at limit', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });

  test('initialising over maxNum shows error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value',
      },
      {
        id: '4',
        type: 'test_block_b',
        value: 'Fourth value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertShowingErrorMessage();
  });

  test('addSibling capability works', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    const addSibling =
      boundBlock.children[0].block.parentCapabilities.get('addSibling');
    expect(addSibling.getBlockMax('test_block_a')).toBeUndefined();
    expect(addSibling.getBlockMax()).toEqual(3);
    expect(addSibling.getBlockCount()).toEqual(2);
    addSibling.fn({ type: 'test_block_a' });
    expect(boundBlock.children.length).toEqual(3);
    expect(boundBlock.children[1].type).toEqual('test_block_a');
  });

  test('insert at limit triggers error', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertNotShowingErrorMessage();

    boundBlock.insert(
      {
        id: '4',
        type: 'test_block_b',
        value: 'Fourth value',
      },
      2,
    );

    assertCanAddBlock();
    assertShowingErrorMessage();
  });

  test('delete removes error mesage', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_b',
        value: 'Third value',
      },
      {
        id: '4',
        type: 'test_block_b',
        value: 'Fourth value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertShowingErrorMessage();

    boundBlock.deleteBlock(2);

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with minNum set', () => {
  // Define a test block
  const blockDef = new StreamBlockDefinition(
    '',
    [
      [
        '',
        [
          new FieldBlockDefinition(
            'test_block_a',
            new DummyWidgetDefinition('Block A widget'),
            {
              label: 'Test Block <A>',
              required: true,
              icon: 'placeholder',
              classname: 'w-field w-field--char_field w-field--text_input',
            },
          ),
          new FieldBlockDefinition(
            'test_block_b',
            new DummyWidgetDefinition('Block B widget'),
            {
              label: 'Test Block <B>',
              required: true,
              icon: 'pilcrow',
              classname:
                'w-field w-field--char_field w-field--admin_auto_height_text_input',
            },
          ),
        ],
      ],
    ],
    {
      test_block_a: 'Block A options',
      test_block_b: 'Block B options',
    },
    {
      label: '',
      required: true,
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>plenty</strong> of these',
      helpIcon: '<svg></svg>',
      maxNum: null,
      minNum: 2,
      blockCounts: {},
      strings: {
        MOVE_UP: 'Move up',
        MOVE_DOWN: 'Move down',
        DRAG: 'Drag',
        DELETE: 'Delete & kill with fire',
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

  test('test no error message when at lower limit', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertNotShowingErrorMessage();
  });

  test('initialising under minNum shows error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertShowingErrorMessage();
  });

  test('inserting to reach lower limit removes error', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertShowingErrorMessage();

    boundBlock.insert(
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      1,
    );

    assertNotShowingErrorMessage();
  });

  test('deleting to under lower limit shows error mesage', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertNotShowingErrorMessage();

    boundBlock.deleteBlock(1);

    assertShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with blockCounts.max_num set', () => {
  // Define a test block
  const blockDef = new StreamBlockDefinition(
    '',
    [
      [
        '',
        [
          new FieldBlockDefinition(
            'test_block_a',
            new DummyWidgetDefinition('Block A widget'),
            {
              label: 'Test Block <A>',
              required: true,
              icon: 'placeholder',
              classname: 'w-field w-field--char_field w-field--text_input',
            },
          ),
          new FieldBlockDefinition(
            'test_block_b',
            new DummyWidgetDefinition('Block B widget'),
            {
              label: 'Test Block <B>',
              required: true,
              icon: 'pilcrow',
              classname:
                'w-field w-field--char_field w-field--admin_auto_height_text_input',
            },
          ),
        ],
      ],
    ],
    {
      test_block_a: 'Block A options',
      test_block_b: 'Block B options',
    },
    {
      label: '',
      required: true,
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>plenty</strong> of these',
      helpIcon: '<svg></svg>',
      maxNum: null,
      minNum: null,
      blockCounts: {
        test_block_a: {
          max_num: 2,
        },
      },
      strings: {
        MOVE_UP: 'Move up',
        MOVE_DOWN: 'Move down',
        DRAG: 'Drag',
        DELETE: 'Delete & kill with fire',
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

    // Test menu item
    expect(document.querySelector('[role="listbox"]').innerHTML).toContain(
      'Test Block &lt;A&gt;',
    );
  };

  const assertShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical').innerHTML).toBe(
      'Test Block &lt;A&gt;: The maximum number of items is 2',
    );
  };

  const assertNotShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical')).toBe(null);
  };

  test('addSibling capability works', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    assertNotShowingErrorMessage();
    const addSibling =
      boundBlock.children[0].block.parentCapabilities.get('addSibling');
    expect(addSibling.getBlockMax('test_block_a')).toEqual(2);
    expect(addSibling.getBlockCount('test_block_a')).toEqual(1);
    addSibling.fn({ type: 'test_block_a' });
    expect(boundBlock.children.length).toEqual(3);
    expect(boundBlock.children[1].type).toEqual('test_block_a');
    assertNotShowingErrorMessage();
  });

  test('single instance allows creation of new block and duplication', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });

  test('initialising at max_num retains ability to add new block of that type', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_a',
        value: 'Third value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });

  test('insert retains ability to add new block', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertNotShowingErrorMessage();

    boundBlock.insert(
      {
        id: '3',
        type: 'test_block_a',
        value: 'Third value',
      },
      2,
    );

    assertCanAddBlock();
    assertNotShowingErrorMessage();

    boundBlock.insert(
      {
        id: '4',
        type: 'test_block_a',
        value: 'Fourth value',
      },
      2,
    );

    assertCanAddBlock();
    assertShowingErrorMessage();
  });

  test('delete removes error message and does not change availability of new block', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_a',
        value: 'Third value',
      },
      {
        id: '4',
        type: 'test_block_a',
        value: 'Fourth value',
      },
    ]);
    boundBlock.inserters[0].open();

    assertCanAddBlock();
    assertShowingErrorMessage();

    boundBlock.deleteBlock(2);

    assertCanAddBlock();
    assertNotShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with blockCounts.min_num set', () => {
  // Define a test block
  const blockDef = new StreamBlockDefinition(
    '',
    [
      [
        '',
        [
          new FieldBlockDefinition(
            'test_block_a',
            new DummyWidgetDefinition('Block A widget'),
            {
              label: 'Test Block <A>',
              required: true,
              icon: 'placeholder',
              classname: 'w-field w-field--char_field w-field--text_input',
            },
          ),
          new FieldBlockDefinition(
            'test_block_b',
            new DummyWidgetDefinition('Block B widget'),
            {
              label: 'Test Block <B>',
              required: true,
              icon: 'pilcrow',
              classname:
                'w-field w-field--char_field w-field--admin_auto_height_text_input',
            },
          ),
        ],
      ],
    ],
    {
      test_block_a: 'Block A options',
      test_block_b: 'Block B options',
    },
    {
      label: '',
      required: true,
      icon: 'placeholder',
      classname: null,
      helpText: 'use <strong>plenty</strong> of these',
      helpIcon: '<svg></svg>',
      maxNum: null,
      minNum: null,
      blockCounts: {
        test_block_a: {
          min_num: 2,
        },
      },
      strings: {
        MOVE_UP: 'Move up',
        MOVE_DOWN: 'Move down',
        DRAG: 'Drag',
        DELETE: 'Delete & kill with fire',
        DUPLICATE: 'Duplicate',
        ADD: 'Add',
      },
    },
  );

  const assertShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical').innerHTML).toBe(
      'Test Block &lt;A&gt;: The minimum number of items is 2',
    );
  };

  const assertNotShowingErrorMessage = () => {
    expect(document.querySelector('p.help-block.help-critical')).toBe(null);
  };

  test('inserting block to get count above min_num removes error mesage', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
    ]);

    assertShowingErrorMessage();

    boundBlock.insert(
      {
        id: '3',
        type: 'test_block_a',
        value: 'Third value',
      },
      2,
    );

    assertNotShowingErrorMessage();
  });

  test('deleting block to get count below min_num shows error message', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const boundBlock = blockDef.render($('#placeholder'), 'the-prefix', [
      {
        id: '1',
        type: 'test_block_a',
        value: 'First value',
      },
      {
        id: '2',
        type: 'test_block_b',
        value: 'Second value',
      },
      {
        id: '3',
        type: 'test_block_a',
        value: 'Third value',
      },
    ]);

    assertNotShowingErrorMessage();

    boundBlock.deleteBlock(2);

    assertShowingErrorMessage();
  });
});

describe('telepath: wagtail.blocks.StreamBlock with unique block type', () => {
  let boundBlock;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    const blockDef = new StreamBlockDefinition(
      '',
      [
        [
          '',
          [
            new FieldBlockDefinition(
              'test_block_a',
              new DummyWidgetDefinition('Block A widget'),
              {
                label: 'Test Block A',
                required: true,
                icon: 'placeholder',
                classname: 'w-field w-field--char_field w-field--text_input',
              },
            ),
          ],
        ],
      ],
      {
        test_block_a: 'Block A options',
      },
      {
        label: '',
        required: true,
        icon: 'placeholder',
        classname: null,
        helpText: 'use <strong>plenty</strong> of this',
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
    boundBlock = blockDef.render($('#placeholder'), 'the-prefix', []);
  });

  test('it renders correctly without combobox', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('[role="listbox"]')).toBe(null);
    expect(boundBlock.children.length).toEqual(0);
  });

  test('it can add block', () => {
    boundBlock.inserters[0].addButton.click();

    expect(document.body.innerHTML).toMatchSnapshot();
    expect(boundBlock.children.length).toEqual(1);
    expect(boundBlock.children[0].type).toEqual('test_block_a');
  });
});
