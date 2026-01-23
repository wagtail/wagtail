import { createEditorStateFromRaw } from 'draftail';
import { EditorState } from 'draft-js';
import ReactTestUtils from 'react-dom/test-utils';

require('./draftail');

describe('draftail', () => {
  it('exposes a stable API', () => {
    expect(window.draftail).toMatchInlineSnapshot(`
      {
        "DocumentModalWorkflowSource": [Function],
        "DraftUtils": {
          "addHorizontalRuleRemovingSelection": [Function],
          "addLineBreak": [Function],
          "applyMarkdownStyle": [Function],
          "getCommandPalettePrompt": [Function],
          "getEntitySelection": [Function],
          "getEntityTypeStrategy": [Function],
          "getSelectedBlock": [Function],
          "getSelectionEntity": [Function],
          "handleDeleteAtomic": [Function],
          "handleHardNewline": [Function],
          "handleNewLine": [Function],
          "insertNewUnstyledBlock": [Function],
          "removeBlock": [Function],
          "removeBlockEntity": [Function],
          "removeCommandPalettePrompt": [Function],
          "resetBlockWithType": [Function],
          "updateBlockEntity": [Function],
        },
        "DraftailRichTextArea": [Function],
        "EmbedModalWorkflowSource": [Function],
        "ImageModalWorkflowSource": [Function],
        "LinkModalWorkflowSource": [Function],
        "ModalWorkflowSource": [Function],
        "Tooltip": [Function],
        "TooltipEntity": [Function],
        "initEditor": [Function],
        "registerPlugin": [Function],
        "splitState": [Function],
      }
    `);
  });

  it('exposes package as global', () => {
    expect(window.Draftail).toBeDefined();
  });

  it('has default entities registered', () => {
    expect(
      Object.keys(window.draftail.registerPlugin({}, 'entityTypes')),
    ).toEqual(['DOCUMENT', 'LINK', 'IMAGE', 'EMBED', 'undefined']);
  });
});

describe('Calling initEditor via event dispatching', () => {
  const initEditor = window.draftail.initEditor;

  beforeAll(() => {
    /* eslint-disable no-console */
    // mock console.error to ensure it does not bubble to the logs
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(window.draftail, 'initEditor').mockImplementation(() => {});
  });

  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('should support creating a new editor with event dispatching', async () => {
    expect(window.draftail.initEditor).not.toHaveBeenCalled();

    document.body.innerHTML = '<main><input id="editor"></main>';

    document.getElementById('editor').dispatchEvent(
      new CustomEvent('w-draftail:init', {
        bubbles: true,
        cancelable: false,
        detail: { some: 'detail' },
      }),
    );

    expect(console.error).toHaveBeenCalledTimes(0);
    expect(window.draftail.initEditor).toHaveBeenCalledTimes(1);
    expect(window.draftail.initEditor).toHaveBeenLastCalledWith(
      '#editor',
      { some: 'detail' },
      null,
    );
  });

  it('should not call initEditor & show an error in the console if the event has been dispatched incorrectly', async () => {
    expect(window.draftail.initEditor).not.toHaveBeenCalled();

    document.dispatchEvent(
      new CustomEvent('w-draftail:init', {
        bubbles: true,
        cancelable: false,
        detail: { some: 'detail' },
      }),
    );

    expect(console.error).toHaveBeenCalledTimes(1);
    expect(console.error).toHaveBeenCalledWith(
      '`w-draftail:init` event must have a target with an id.',
    );

    expect(window.draftail.initEditor).not.toHaveBeenCalled();
  });

  afterAll(() => {
    console.error.mockRestore();
    window.draftail.initEditor.mockRestore();
  });
});

describe('importing the module multiple times', () => {
  it('should run the init function once if the script is included multiple times', async () => {
    // Imported at the top level (similar to the initial page load)
    const firstDraftail = window.draftail;

    // Subsequent imports (e.g. in AJAX responses)
    jest.isolateModules(() => {
      // Ensure stubs are loaded in the new isolated context
      require('../../../tests/stubs');
      require('./draftail');
    });

    // Should be the same instance
    const secondDraftail = window.draftail;
    expect(secondDraftail).toBe(firstDraftail);

    jest.isolateModules(() => {
      require('./draftail');
    });

    const thirdDraftail = window.draftail;
    expect(thirdDraftail).toBe(firstDraftail);

    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(window.draftail, 'initEditor').mockImplementation(() => {});

    expect(window.draftail.initEditor).not.toHaveBeenCalled();

    document.body.innerHTML = '<main><input id="editor"></main>';

    document.getElementById('editor').dispatchEvent(
      new CustomEvent('w-draftail:init', {
        bubbles: true,
        cancelable: false,
        detail: { some: 'detail' },
      }),
    );

    expect(console.error).toHaveBeenCalledTimes(0);

    // Should only be called once. If the script isn't written correctly, then
    // the window.draftail object would be a new instance every time, or
    // the initEditor function would be called multiple times.
    expect(window.draftail.initEditor).toHaveBeenCalledTimes(1);
    expect(window.draftail.initEditor).toHaveBeenLastCalledWith(
      '#editor',
      { some: 'detail' },
      null,
    );

    /* eslint-enable no-console */
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });
});

describe('DraftailRichTextArea', () => {
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

    const widgetDef = new window.draftail.DraftailRichTextArea({
      entityTypes: [
        {
          type: 'LINK',
          icon: 'link',
          description: 'Link',
          attributes: ['url', 'id', 'parentId'],
          allowlist: {
            href: '^(http:|https:|undefined$)',
          },
        },
        {
          type: 'IMAGE',
          icon: 'image',
          description: 'Image',
          attributes: ['id', 'src', 'alt', 'format'],
          allowlist: {
            id: true,
          },
        },
      ],
      enableHorizontalRule: true,
      inlineStyles: [
        {
          type: 'BOLD',
          icon: 'bold',
          description: 'Bold',
        },
        {
          type: 'ITALIC',
          icon: 'italic',
          description: 'Italic',
        },
      ],
      blockTypes: [
        {
          label: 'H2',
          type: 'header-two',
          description: 'Heading 2',
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

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(inputElement.getAttribute('aria-invalid')).toBe('true');
    boundWidget.setInvalid(false);
    expect(inputElement.getAttribute('aria-invalid')).toBeNull();
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
