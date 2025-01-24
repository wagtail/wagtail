import '../draftail';
import './telepath';
import './widgets';

import $ from 'jquery';
import { createEditorStateFromRaw } from 'draftail';
import { EditorState } from 'draft-js';

import ReactTestUtils from 'react-dom/test-utils';

window.$ = $;

window.comments = {
  getContentPath: jest.fn(),
};

describe('telepath: wagtail.widgets.Widget', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Widget',
      _args: [
        '<input type="text" name="__NAME__" maxlength="255" id="__ID__">',
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('The Value');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('The Value');
    document.querySelector('input').value = 'New Value';
    expect(boundWidget.getValue()).toBe('New Value');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('The Value');
    document.querySelector('input').value = 'New Value';
    expect(boundWidget.getState()).toBe('New Value');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('The new Value');
    expect(document.querySelector('input').value).toBe('The new Value');
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });

  test('it should support options with attributes', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
      {},
      {
        attributes: {
          'maxLength': 512,
          'aria-describedby': 'some-id',
          'required': '',
        },
      },
    );

    const input = document.querySelector('input');

    expect(input.maxLength).toBe(512);
    expect(input.getAttribute('aria-describedby')).toBe('some-id');
    expect(input.required).toBe(true);
  });
});

describe('telepath: wagtail.widgets.Widget with inline JS', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Widget',
      _args: [
        '<div><input type="text" name="__NAME__" maxlength="255" id="__ID__"><script>document.getElementById("__ID__").className = "custom-class";</script></div>',
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.querySelector('input').outerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id" class="custom-class">',
    );
    expect(document.querySelector('input').value).toBe('The Value');
  });
});

describe('telepath: wagtail.widgets.Widget with multiple top-level nodes', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Widget',
      _args: [
        '<!-- here comes a widget --><input type="text" name="__NAME__" maxlength="255" id="__ID__"><button data-button-state="idle">Click me</button><script>document.getElementById("__ID__").className = "custom-class";</script>',
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.querySelector('input').outerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id" class="custom-class">',
    );
    expect(document.querySelector('[data-button-state]').outerHTML).toBe(
      '<button data-button-state="idle">Click me</button>',
    );
    expect(document.querySelector('input').value).toBe('The Value');
  });
});

describe('telepath: wagtail.widgets.RadioSelect', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.RadioSelect',
      _args: [
        `<ul id="__ID__">
          <li>
            <label for="__ID___0">
            <input type="radio" name="__NAME__" value="tea" id="__ID___0"> Tea</label>
          </li>
          <li>
            <label for="__ID___1">
            <input type="radio" name="__NAME__" value="coffee" id="__ID___1"> Coffee</label>
          </li>
        </ul>`,
        '__ID___0',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['tea'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[value="tea"]').checked).toBe(true);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(false);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('tea');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['tea']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['coffee']);
    expect(document.querySelector('input[value="tea"]').checked).toBe(false);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(true);
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('input[value="tea"]'),
    );
  });
});

describe('telepath: wagtail.widgets.RadioSelect for CheckboxSelectMultiple', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.RadioSelect',
      _args: [
        `<ul id="__ID__">
          <li>
            <label for="__ID___0">
            <input type="checkbox" name="__NAME__" value="red" id="__ID___0"> Red</label>
          </li>
          <li>
            <label for="__ID___1">
            <input type="checkbox" name="__NAME__" value="green" id="__ID___1"> Green</label>
          </li>
          <li>
            <label for="__ID___2">
            <input type="checkbox" name="__NAME__" value="blue" id="__ID___2"> Blue</label>
          </li>
        </ul>`,
        '__ID___0',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['red', 'blue'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[value="red"]').checked).toBe(true);
    expect(document.querySelector('input[value="green"]').checked).toBe(false);
    expect(document.querySelector('input[value="blue"]').checked).toBe(true);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toStrictEqual(['red', 'blue']);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['red', 'blue']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['red', 'green']);
    expect(document.querySelector('input[value="red"]').checked).toBe(true);
    expect(document.querySelector('input[value="green"]').checked).toBe(true);
    expect(document.querySelector('input[value="blue"]').checked).toBe(false);
  });
});

describe('telepath: wagtail.widgets.CheckboxInput', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.CheckboxInput',
      _args: ['<input type="checkbox" name="__NAME__" id="__ID__">', '__ID__'],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'sugar',
      'id-sugar',
      true,
    );
  });

  test('it renders correctly', () => {
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(true);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe(true);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe(true);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(false);
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(false);
    boundWidget.setState(true);
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(true);
  });

  test('focus() focuses the checkbox', () => {
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('input[id="id-sugar"]'),
    );
  });
});

describe('telepath: wagtail.widgets.Select', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Select',
      _args: [
        `<select name="__NAME__" id="__ID__">
          <option value="1">Option 1</option>
          <option value="2">Option 2</option>
        </select>`,
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['1'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    const select = document.querySelector('select');
    expect(select.options[select.selectedIndex].value).toBe('1');
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(1);
    expect(selectedOptions[0].value).toBe('1');
  });

  test('getTextLabel() returns the text of selected option', () => {
    expect(boundWidget.getTextLabel()).toBe('Option 1');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('1');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['1']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['2']);
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(1);
    expect(selectedOptions[0].value).toBe('2');
  });
});

describe('telepath: wagtail.widgets.Select multiple', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Select',
      _args: [
        `<select name="__NAME__" id="__ID__" multiple>
          <option value="red">Red</option>
          <option value="green">Green</option>
          <option value="blue">Blue</option>
        </select>`,
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['red', 'blue'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    const select = document.querySelector('select');
    expect(select.options[select.selectedIndex].value).toBe('red');
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(2);
    expect(selectedOptions[0].value).toBe('red');
    expect(selectedOptions[1].value).toBe('blue');
  });

  test('getTextLabel() returns the text of selected options', () => {
    expect(boundWidget.getTextLabel()).toBe('Red, Blue');
  });

  test('getValue() returns the current values', () => {
    expect(boundWidget.getValue()).toStrictEqual(['red', 'blue']);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['red', 'blue']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['red', 'green']);
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(2);
    expect(selectedOptions[0].value).toBe('red');
    expect(selectedOptions[1].value).toBe('green');
  });
});

describe('telepath: wagtail.widgets.DraftailRichTextArea', () => {
  let boundWidget;
  let inputElement;
  let parentCapabilities;

  const TEST_RAW = {
    blocks: [
      {
        key: 't30wm',
        type: 'unstyled',
        depth: 0,
        text: 'Test Bold Italic',
        inlineStyleRanges: [
          {
            offset: 5,
            length: 4,
            style: 'BOLD',
          },
          {
            offset: 10,
            length: 6,
            style: 'ITALIC',
          },
        ],
        entityRanges: [],
      },
    ],
    entityMap: {},
  };
  const TEST_VALUE = JSON.stringify(TEST_RAW);

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.DraftailRichTextArea',
      _args: [
        {
          entityTypes: [
            {
              _dict: {
                type: 'LINK',
                icon: 'link',
                description: 'Link',
                attributes: ['url', 'id', 'parentId'],
                allowlist: {
                  href: '^(http:|https:|undefined$)',
                },
              },
            },
            {
              _dict: {
                type: 'IMAGE',
                icon: 'image',
                description: 'Image',
                attributes: ['id', 'src', 'alt', 'format'],
                allowlist: {
                  id: true,
                },
              },
            },
          ],
          enableHorizontalRule: true,
          inlineStyles: [
            {
              _dict: {
                type: 'BOLD',
                icon: 'bold',
                description: 'Bold',
              },
            },
            {
              _dict: {
                type: 'ITALIC',
                icon: 'italic',
                description: 'Italic',
              },
            },
          ],
          blockTypes: [
            {
              _dict: {
                label: 'H2',
                type: 'header-two',
                description: 'Heading 2',
              },
            },
          ],
        },
      ],
    });
    parentCapabilities = new Map();
    parentCapabilities.set('split', { enabled: true, fn: jest.fn() });
    parentCapabilities.set('addSibling', {
      enabled: true,
      getBlockMax: () => 5,
      blockGroups: [
        [
          'Media',
          [
            {
              name: 'image_block',
              meta: {
                icon: 'image',
                label: 'Image',
                blockDefId: 'blockdef-1234',
                isPreviewable: true,
                description: 'Full-width image',
              },
            },
          ],
        ],
      ],
      fn: jest.fn(),
    });
    const inputId = 'the-id';
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      inputId,
      TEST_VALUE,
      parentCapabilities,
      {
        attributes: {
          maxLength: 512,
        },
      },
    );
    inputElement = document.querySelector('#the-id');
  });

  test('it renders correctly', () => {
    expect(document.querySelector('.Draftail-Editor__wrapper')).toBeTruthy();
    expect(document.querySelector('input').value).toBe(TEST_VALUE);
    expect(document.querySelector('input').maxLength).toBe(512);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe(TEST_VALUE);
  });

  test('getState() returns the current state', () => {
    const state = createEditorStateFromRaw(TEST_RAW);
    let retrievedState = boundWidget.getState();
    // Ignore selection, which is altered from the original state by Draftail,
    // (TODO: figure out why this happens)
    // and decorator, which is added to by CommentableEditor
    retrievedState = EditorState.acceptSelection(
      retrievedState,
      state.getSelection(),
    );
    retrievedState = EditorState.set(retrievedState, {
      decorator: state.getDecorator(),
    });
    expect(retrievedState).toStrictEqual(state);
  });

  test('setState() changes the current state', () => {
    const NEW_VALUE = {
      blocks: [
        {
          key: 't30wm',
          type: 'unstyled',
          depth: 0,
          text: 'New value',
          inlineStyleRanges: [],
          entityRanges: [],
        },
      ],
      entityMap: {},
    };
    const NEW_STATE = createEditorStateFromRaw(NEW_VALUE);
    boundWidget.setState(NEW_STATE);

    let retrievedState = boundWidget.getState();
    // Ignore selection, which is altered from the original state by Draftail,
    // and decorator, which is added to by CommentableEditor
    retrievedState = EditorState.acceptSelection(
      retrievedState,
      NEW_STATE.getSelection(),
    );
    retrievedState = EditorState.set(retrievedState, {
      decorator: NEW_STATE.getDecorator(),
    });
    expect(retrievedState).toStrictEqual(NEW_STATE);
  });

  test('focus() focuses the text input', () => {
    // focus happens on a timeout, so use a mock to make it happen instantly
    jest.useFakeTimers();
    boundWidget.focus();
    jest.runAllTimers();
    expect(document.activeElement).toBe(
      document.querySelector('.public-DraftEditor-content'),
    );
  });

  test('setCapabilityOptions for split updates the editor commands', () => {
    ReactTestUtils.act(() =>
      boundWidget.setCapabilityOptions('split', { enabled: false }),
    );
    expect(inputElement.draftailEditor.props.commands).toHaveLength(2);
    ReactTestUtils.act(() =>
      boundWidget.setCapabilityOptions('split', { enabled: true }),
    );
    expect(inputElement.draftailEditor.props.commands).toHaveLength(4);
    expect(inputElement.draftailEditor.props.commands[3].items[0].type).toBe(
      'split',
    );
  });

  test('configures the block chooser based on siblings capability', () => {
    expect(inputElement.draftailEditor.props.commands[2].items[0]).toEqual(
      expect.objectContaining({
        icon: 'image',
        label: 'Image',
        blockDefId: 'blockdef-1234',
        isPreviewable: true,
        description: 'Full-width image',
      }),
    );
  });
});

describe('telepath: wagtail.widgets.DateInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initDateChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.AdminDateInput',
      _args: [
        {
          dayOfWeekStart: 0,
          format: 'Y-m-d',
        },
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '2021-01-19',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('2021-01-19');
  });

  test('window.initDateChooser was called', () => {
    expect(window.initDateChooser.mock.calls.length).toBe(1);
    expect(window.initDateChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initDateChooser.mock.calls[0][1]).toEqual({
      dayOfWeekStart: 0,
      format: 'Y-m-d',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('2021-01-19');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('2021-01-19');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('2021-01-20');
    expect(document.querySelector('input').value).toBe('2021-01-20');
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('telepath: wagtail.widgets.TimeInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initTimeChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.AdminTimeInput',
      _args: [
        {
          format: 'H:i',
          formatTime: 'H:i',
        },
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '11:59',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('11:59');
  });

  test('window.initTimeChooser was called', () => {
    expect(window.initTimeChooser.mock.calls.length).toBe(1);
    expect(window.initTimeChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initTimeChooser.mock.calls[0][1]).toEqual({
      format: 'H:i',
      formatTime: 'H:i',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('11:59');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('11:59');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('12:34');
    expect(document.querySelector('input').value).toBe('12:34');
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('telepath: wagtail.widgets.DateTimeInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initDateTimeChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.AdminDateTimeInput',
      _args: [
        {
          dayOfWeekStart: 0,
          format: 'Y-m-d H:i',
          formatTime: 'H:i',
        },
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '2021-01-19 11:59',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('2021-01-19 11:59');
  });

  test('window.initDateTimeChooser was called', () => {
    expect(window.initDateTimeChooser.mock.calls.length).toBe(1);
    expect(window.initDateTimeChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initDateTimeChooser.mock.calls[0][1]).toEqual({
      dayOfWeekStart: 0,
      format: 'Y-m-d H:i',
      formatTime: 'H:i',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('2021-01-19 11:59');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('2021-01-19 11:59');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('2021-01-20 12:34');
    expect(document.querySelector('input').value).toBe('2021-01-20 12:34');
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });

  test('getTextLabel() returns the text of entered value', () => {
    expect(boundWidget.getTextLabel()).toBe('2021-01-19 11:59');
  });
});
