import '../page-chooser';
import '../draftail';
import './telepath';
import './widgets';

import { createEditorStateFromRaw } from 'draftail';
import { EditorState } from 'draft-js';

import ReactTestUtils from 'react-dom/test-utils';
import $ from 'jquery';

window.$ = $;

window.comments = {
  getContentPath: jest.fn(),
};
window.draftail.getSplitControl = jest.fn(window.draftail.getSplitControl);

describe('telepath: wagtail.widgets.Widget', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a simple text block widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Widget',
      _args: [
        '<input type="text" name="__NAME__" maxlength="255" id="__ID__">',
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      $('#placeholder'),
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
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('The Value');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('The new Value');
    expect(document.querySelector('input').value).toBe('The new Value');
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('telepath: wagtail.widgets.RadioSelect', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a radio select widget
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
      $('#placeholder'),
      'the-name',
      'the-id',
      'tea',
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
    expect(boundWidget.getState()).toBe('tea');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('coffee');
    expect(document.querySelector('input[value="tea"]').checked).toBe(false);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(true);
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();

    // Note: This widget always focuses the last element
    expect(document.activeElement).toBe(
      document.querySelector('input[value="coffee"]'),
    );
  });
});

describe('telepath: wagtail.widgets.CheckboxInput', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a radio select widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.CheckboxInput',
      _args: ['<input type="checkbox" name="__NAME__" id="__ID__">', '__ID__'],
    });
    boundWidget = widgetDef.render(
      $('#placeholder'),
      'sugar',
      'id-sugar',
      true,
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
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

    // Unpack and render a radio select widget
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
      $('#placeholder'),
      'the-name',
      'the-id',
      '1',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    const select = document.querySelector('select');
    expect(select.options[select.selectedIndex].value).toBe('1');
  });

  test('getTextLabel() returns the text of selected option', () => {
    expect(boundWidget.getTextLabel()).toBe('Option 1');
  });
});

describe('telepath: wagtail.widgets.PageChooser', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a radio select widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.PageChooser',
      _args: [
        `<div id="__ID__-chooser" class="chooser page-chooser blank" data-chooser-url="/admin/choose-page/">
          <div class="chosen">
            <span class="title"></span>
            <ul class="actions">
              <li>
                <button type="button" class="button action-choose button-small button-secondary">
                  Choose another page
                </button>
              </li>
              <li>
                <a href=""
                   class="edit-link button button-small button-secondary"
                   target="_blank"
                   rel="noreferrer">
                  Edit this page
                </a>
              </li>
            </ul>
          </div>
          <div class="unchosen">
            <button type="button" class="button action-choose button-small button-secondary">
              Choose a page
            </button>
          </div>
        </div>
        <input type="hidden" name="__NAME__" id="__ID__">`,
        '__ID__',
        {
          model_names: ['wagtailcore.page'],
          can_choose_root: false,
          user_perms: null,
        },
      ],
    });
    boundWidget = widgetDef.render($('#placeholder'), 'the-name', 'the-id', {
      id: 60,
      parentId: 1,
      adminTitle: 'Welcome to the Wagtail Bakery!',
      editUrl: '/admin/pages/60/edit/',
    });
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('60');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe(60);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toEqual({
      id: 60,
      parentId: 1,
      adminTitle: 'Welcome to the Wagtail Bakery!',
      editUrl: '/admin/pages/60/edit/',
    });
  });

  test('setState() changes the current page', () => {
    boundWidget.setState({
      id: 34,
      parentId: 3,
      adminTitle: 'Anadama',
      editUrl: '/admin/pages/34/edit/',
    });
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('34');
  });

  test('setState() to null clears the fields', () => {
    boundWidget.setState(null);
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('');
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();

    // Note: This widget always focuses the unchosen button, even if it has a value
    expect(document.activeElement).toBe(
      document.querySelector('.unchosen button'),
    );
  });
});

describe('telepath: wagtail.widgets.AdminAutoHeightTextInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.autosize = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a textarea using the AdminAutoHeightTextInput widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.AdminAutoHeightTextInput',
      _args: [
        '<textarea name="__NAME__" cols="40" rows="1" id="__ID__"></textarea>',
        '__ID__',
      ],
    });
    boundWidget = widgetDef.render(
      $('#placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<textarea name="the-name" cols="40" rows="1" id="the-id"></textarea>',
    );
    expect(document.querySelector('textarea').value).toBe('The Value');
  });

  test('window.autosize was called', () => {
    expect(window.autosize.mock.calls.length).toBe(1);
    expect(window.autosize.mock.calls[0][0].get(0)).toBe(
      document.querySelector('textarea'),
    );
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('The Value');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('The Value');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('The new Value');
    expect(document.querySelector('textarea').value).toBe('The new Value');
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('textarea'));
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

    // Unpack and render a Draftail input
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
    const inputId = 'the-id';
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      inputId,
      TEST_VALUE,
      parentCapabilities,
    );
    inputElement = document.querySelector('#the-id');
  });

  test('it renders correctly', () => {
    expect(document.querySelector('.Draftail-Editor__wrapper')).toBeTruthy();
    expect(document.querySelector('input').value).toBe(TEST_VALUE);
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

  test('setCapabilityOptions for split updates the editor controls', () => {
    ReactTestUtils.act(() =>
      boundWidget.setCapabilityOptions('split', { enabled: false }),
    );
    expect(inputElement.draftailEditor.props.controls).toHaveLength(2);
    expect(window.draftail.getSplitControl).toHaveBeenLastCalledWith(
      parentCapabilities.get('split').fn,
      false,
    );
    ReactTestUtils.act(() =>
      boundWidget.setCapabilityOptions('split', { enabled: true }),
    );
    expect(inputElement.draftailEditor.props.controls).toHaveLength(2);
    expect(window.draftail.getSplitControl).toHaveBeenLastCalledWith(
      parentCapabilities.get('split').fn,
      true,
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
      $('#placeholder'),
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
      $('#placeholder'),
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
      $('#placeholder'),
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
});
