import $ from 'jquery';

window.$ = $;

import '../../admin/telepath/telepath';
import './table';

const TEST_OPTIONS = {
  minSpareRows: 0,
  startRows: 3,
  startCols: 3,
  colHeaders: false,
  rowHeaders: false,
  contextMenu: [
    'row_above',
    'row_below',
    '---------',
    'col_left',
    'col_right',
    '---------',
    'remove_row',
    'remove_col',
    '---------',
    'undo',
    'redo',
  ],
  editor: 'text',
  stretchH: 'all',
  height: 108,
  renderer: 'text',
  autoColumnSize: false,
  language: 'en-us',
};

const TEST_STRINGS = {
  'Row header': 'Row header',
  'Display the first row as a header.': 'Display the first row as a header.',
  'Column header': 'Column header',
  'Display the first column as a header.':
    'Display the first column as a header.',
  'Table caption': 'Table caption',

  'A heading that identifies the overall topic of the table, and is useful for screen reader users':
    'A heading that identifies the overall topic of the table, and is useful for screen reader users',
  'Table': 'Table',
};

const TEST_VALUE = {
  data: [
    ['Test', 'Heading'],
    ['Foo', '123'],
    ['Bar', '456'],
  ],
  cell: [],
  first_row_is_table_header: true,
  first_col_is_header: false,
  table_caption: '',
};

// Note: Tests both TableInput and initTable together as this is the only supported way to use them
// It does, however, mock out Handsontable itself
describe('telepath: wagtail.widgets.TableInput', () => {
  // These settings are passed into the table when rendered
  // They are reset for each test so that you can modify them
  let testOptions;
  let testStrings;
  let testValue;
  let handsontableConstructorMock;

  // Call this to render the table block with the current settings
  const render = () => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a simple text block widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.TableInput',
      _args: [testOptions, testStrings],
    });
    return widgetDef.render($('#placeholder'), 'the-name', 'the-id', testValue);
  };

  beforeEach(() => {
    handsontableConstructorMock = jest.fn();
    window.Handsontable = (...args) => {
      handsontableConstructorMock(...args);
    };
    window.Handsontable.prototype.render = jest.fn();

    // Reset options, strings, and value for each test
    testOptions = JSON.parse(JSON.stringify(TEST_OPTIONS));
    testStrings = JSON.parse(JSON.stringify(TEST_STRINGS));
    testValue = JSON.parse(JSON.stringify(TEST_VALUE));
  });

  test('it renders correctly', () => {
    render();
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[name="the-name"]').value).toEqual(
      JSON.stringify(testValue),
    );
  });

  test('Handsontable constructor is called', () => {
    render();
    expect(handsontableConstructorMock.mock.calls.length).toBe(1);
    expect(handsontableConstructorMock.mock.calls[0][0]).toBe(
      document.getElementById('the-id-handsontable-container'),
    );
    expect(handsontableConstructorMock.mock.calls[0][1].autoColumnSize).toBe(
      false,
    );
    expect(handsontableConstructorMock.mock.calls[0][1].cell).toEqual([]);
    expect(handsontableConstructorMock.mock.calls[0][1].colHeaders).toBe(false);
    expect(handsontableConstructorMock.mock.calls[0][1].contextMenu).toEqual(
      testOptions.contextMenu,
    );
    expect(handsontableConstructorMock.mock.calls[0][1].data).toEqual(
      testValue.data,
    );
    expect(handsontableConstructorMock.mock.calls[0][1].editor).toBe('text');
    expect(handsontableConstructorMock.mock.calls[0][1].height).toBe(108);
    expect(handsontableConstructorMock.mock.calls[0][1].language).toBe('en-us');
    expect(handsontableConstructorMock.mock.calls[0][1].minSpareRows).toBe(0);
    expect(handsontableConstructorMock.mock.calls[0][1].renderer).toBe('text');
    expect(handsontableConstructorMock.mock.calls[0][1].rowHeaders).toBe(false);
    expect(handsontableConstructorMock.mock.calls[0][1].startCols).toBe(3);
    expect(handsontableConstructorMock.mock.calls[0][1].startRows).toBe(3);
    expect(handsontableConstructorMock.mock.calls[0][1].stretchH).toBe('all');
  });

  test('Handsontable.render is called', () => {
    render();
    expect(window.Handsontable.prototype.render.mock.calls.length).toBe(1);
    expect(window.Handsontable.prototype.render.mock.calls[0].length).toBe(0);
  });

  test('translation', () => {
    testStrings = {
      'Row header': 'En-tête de ligne',
      'Display the first row as a header.':
        "Affichez la première ligne sous forme d'en-tête.",
      'Column header': 'En-tête de colonne',
      'Display the first column as a header.':
        "Affichez la première colonne sous forme d'en-tête.",
      'Table caption': 'Légende du tableau',

      'A heading that identifies the overall topic of the table, and is useful for screen reader users':
        "Un en-tête qui identifie le sujet général du tableau et qui est utile pour les utilisateurs de lecteurs d'écran",
      'Table': 'Tableau',
    };
    render();
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('getValue() returns the current value', () => {
    const boundWidget = render();
    expect(boundWidget.getValue()).toEqual(TEST_VALUE);
  });

  test('getState() returns the current value', () => {
    const boundWidget = render();
    expect(boundWidget.getState()).toEqual(TEST_VALUE);
  });

  test('setState() changes the current state', () => {
    const boundWidget = render();
    testValue.data.push(['Baz', '789']);
    boundWidget.setState(testValue);
    expect(document.querySelector('input[name="the-name"]').value).toEqual(
      JSON.stringify(testValue),
    );
  });
});
