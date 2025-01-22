import '../../admin/telepath/telepath';
import $ from 'jquery';
import { TypedTableBlockDefinition } from './typed_table_block';
import { FieldBlockDefinition } from '../../../components/StreamField/blocks/FieldBlock';
import { StreamBlockDefinition } from '../../../components/StreamField/blocks/StreamBlock';

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

describe('wagtail.contrib.typed_table_block.blocks.TypedTableBlock', () => {
  let blockDef;
  let boundBlock;
  let childBlockA;
  let childBlockB;

  beforeEach(() => {
    // Create mocks for callbacks
    constructor = jest.fn();
    setState = jest.fn();
    getState = jest.fn();
    getValue = jest.fn();
    focus = jest.fn();

    // Define a test block
    childBlockA = new FieldBlockDefinition(
      'test_block_a',
      new DummyWidgetDefinition('Block A widget'),
      {
        label: 'Test Block A',
        required: true,
        icon: 'placeholder',
        classname: 'w-field w-field--char_field w-field--text_input',
      },
    );
    childBlockB = new FieldBlockDefinition(
      'test_block_b',
      new DummyWidgetDefinition('Block B widget'),
      {
        label: 'Test Block B',
        required: true,
        icon: 'pilcrow',
        classname:
          'w-field w-field--char_field w-field--admin_auto_height_text_input',
      },
    );

    blockDef = new TypedTableBlockDefinition(
      'table',
      [childBlockA, childBlockB],
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
        strings: {
          CAPTION: 'Caption',
          CAPTION_HELP_TEXT:
            'A heading that identifies the overall topic of the table, and is useful for screen reader users.',
          ADD_COLUMN: 'Add column',
          ADD_ROW: 'Add row',
          COLUMN_HEADING: 'Column heading',
          INSERT_COLUMN: 'Insert column',
          DELETE_COLUMN: 'Delete column',
          INSERT_ROW: 'Insert row',
          DELETE_ROW: 'Delete row',
        },
      },
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render(
      document.getElementById('placeholder'),
      'mytable',
      {
        columns: [
          { type: 'test_block_a', heading: 'Item' },
          { type: 'test_block_b', heading: 'Quantity' },
        ],
        rows: [{ values: ['Cheese', 3] }, { values: ['Peas', 5] }],
        caption: 'A shopping list',
      },
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(boundBlock.columns.length).toBe(2);
    expect(boundBlock.rows.length).toBe(2);
    expect(document.getElementsByName('mytable-caption')[0].value).toBe(
      'A shopping list',
    );
  });

  test('can be cleared', () => {
    boundBlock.clear();
    expect(boundBlock.columns.length).toBe(0);
    expect(boundBlock.rows.length).toBe(0);
    expect(document.getElementsByName('mytable-column-count')[0].value).toBe(
      '0',
    );
    expect(document.getElementsByName('mytable-row-count')[0].value).toBe('0');
    expect(document.getElementsByName('mytable-caption')[0].value).toBe('');
  });

  test('supports adding a caption', () => {
    boundBlock.setCaption('A shopping list');
    expect(document.getElementsByName('mytable-caption')[0].value).toBe(
      'A shopping list',
    );
  });

  test('supports inserting columns', () => {
    boundBlock.insertColumn(1, childBlockA);
    expect(boundBlock.columns.length).toBe(3);
    expect(document.getElementsByName('mytable-column-count')[0].value).toBe(
      '3',
    );
  });

  test('supports deleting columns', () => {
    boundBlock.deleteColumn(0);
    expect(boundBlock.columns.length).toBe(1);

    // column count field still counts deleted columns (as it's used by the server-side code
    // to find out the maximum column ID to look for)
    expect(document.getElementsByName('mytable-column-count')[0].value).toBe(
      '2',
    );
  });

  test('counts deleted columns in column-count hidden field', () => {
    boundBlock.deleteColumn(0);
    boundBlock.insertColumn(1, childBlockA);
    expect(boundBlock.columns.length).toBe(2);
    expect(document.getElementsByName('mytable-column-count')[0].value).toBe(
      '3',
    );
  });

  test('supports inserting rows', () => {
    boundBlock.insertRow(1);
    expect(boundBlock.rows.length).toBe(3);
    expect(document.getElementsByName('mytable-row-count')[0].value).toBe('3');
  });

  test('supports deleting rows', () => {
    boundBlock.deleteRow(1);
    expect(boundBlock.rows.length).toBe(1);
    // row count field still counts deleted rows (as it's used by the server-side code
    // to find out the maximum row ID to look for)
    expect(document.getElementsByName('mytable-row-count')[0].value).toBe('2');
  });

  test('counts deleted rows in row-count hidden field', () => {
    boundBlock.deleteRow(0);
    boundBlock.insertRow(0);
    expect(boundBlock.rows.length).toBe(2);
    expect(document.getElementsByName('mytable-row-count')[0].value).toBe('3');
  });

  test('setError passes error messages to children', () => {
    boundBlock.setError({
      blockErrors: {
        0: {
          1: { messages: ['This is not enough cheese.'] },
        },
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

describe('wagtail.contrib.typed_table_block.blocks.TypedTableBlock in StreamBlock', () => {
  let boundBlock;
  let innerStreamDef;

  beforeEach(() => {
    innerStreamDef = new StreamBlockDefinition(
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

    const streamBlockDef = new StreamBlockDefinition(
      '',
      [
        [
          '',
          [
            new TypedTableBlockDefinition(
              'table',
              [innerStreamDef],
              {},
              {
                label: '',
                required: true,
                icon: 'placeholder',
                classname: null,
                helpText: 'use <strong>plenty</strong> of these',
                helpIcon: '<svg></svg>',
                strings: {
                  ADD_COLUMN: 'Add column',
                  ADD_ROW: 'Add row',
                  COLUMN_HEADING: 'Column heading',
                  INSERT_COLUMN: 'Insert column',
                  DELETE_COLUMN: 'Delete column',
                  INSERT_ROW: 'Insert row',
                  DELETE_ROW: 'Delete row',
                },
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
    );

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = streamBlockDef.render($('#placeholder'), 'the-prefix', []);
  });

  test('duplicateBlock does not duplicate stream block ids in typed table blocks', () => {
    // Insert a typed table block at the top level
    boundBlock.insert(
      {
        type: 'table',
        value: { rows: [], columns: [] },
        id: 'old-id-1',
      },
      0,
    );

    const tableBlock = boundBlock.children[0].block;

    // Add a column and row for the nested stream block
    tableBlock.insertColumn(0, innerStreamDef);
    tableBlock.insertRow(0);
    const innerStreamBlock = tableBlock.rows[0].blocks[0];

    // Insert a block into the inner stream
    innerStreamBlock.insert(
      { type: 'test_block_a', value: 'foobar', id: 'old-inner-stream-id-1' },
      0,
    );

    // Duplicate the outermost block (typed table block)
    boundBlock.duplicateBlock(0);

    // Check the ids on the top level blocks
    expect(boundBlock.children[1]).not.toHaveSameBlockIdAs(
      boundBlock.children[0],
    );

    // Check the ids on the nested blocks
    expect(
      boundBlock.children[1].block.rows[0].blocks[0].children[0],
    ).not.toHaveSameBlockIdAs(
      boundBlock.children[0].block.rows[0].blocks[0].children[0],
    );
  });
});
