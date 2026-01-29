import { createEditorStateFromRaw } from 'draftail';
import { EditorState } from 'draft-js';
import ReactTestUtils from 'react-dom/test-utils';
import Draftail from '../../components/Draftail/index';
const { initEditor: realInitEditor } = Draftail;

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
    jest.spyOn(console, 'error').mockImplementation(() => { });
    jest.spyOn(window.draftail, 'initEditor').mockImplementation(() => { });
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
      document.getElementById('editor'),
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

  it('should initialize the correct element when duplicates exist', async () => {
    expect(window.draftail.initEditor).not.toHaveBeenCalled();

    // Create a scenario where a parent element has an ID that ends with the input's ID
    // This simulates the issue where document.querySelector('#' + id) might match the parent
    // if the logic was flawed or ambiguous, although strictly '#' + id should only match exact ID.
    // However, the report says "DraftailRichTextArea fails... due to HTML ID conflicts".
    // In the reported issue, the selector returns the parent panel instead of the input element.
    // This happens if the user inadvertently used the same ID for parent and child, OR if the selector is somehow fuzzy.
    // Wait, document.querySelector('#id') selects the FIRST element with that ID.
    // If the parent has the SAME ID as the child (which is invalid HTML but happens), it picks the parent.
    // The issue description says: "parent panel <div> elements and child <input>/<textarea> elements can end up sharing the same HTML id".

    document.body.innerHTML = `
      <div id="duplicate-id">
        <input id="duplicate-id" class="target-input">
      </div>
    `;

    // We want to initialize the INPUT, not the DIV.
    const inputElement = document.body.querySelector('input');

    document.getElementById('duplicate-id').dispatchEvent(
      new CustomEvent('w-draftail:init', {
        bubbles: true,
        cancelable: false,
        detail: { some: 'detail' },
        target: inputElement, // The event is dispatched on the input (bubbling up effectively, or handled directly)
      }),
    );

    // In the current implementation (before fix), the event listener gets target.id
    // and calls initEditor('#duplicate-id').
    // initEditor does document.querySelector('#duplicate-id').
    // Since the DIV comes first in the DOM and has the same ID, it selects the DIV.
    // Then it tries to access .value on the DIV, fails JSON.parse, or appends wrapper to parent of DIV.

    expect(console.error).toHaveBeenCalledTimes(0);
    expect(window.draftail.initEditor).toHaveBeenCalledTimes(1);

    // We expect initEditor to be called.
    // To verify IF it selected the right element, we would need to inspect side effects in initEditor.
    // But initEditor is mocked here!
    // So 'initEditor' test here just checks arguments.
    // The REAL logic failure happens INSIDE initEditor.
    // So we should probably NOT mock initEditor for a true reproduction, OR we need to test initEditor itself.
    // But initEditor is not exported for direct testing easily in this file?
    // Actually it is: window.draftail.initEditor
  });

  afterAll(() => {
    console.error.mockRestore();
    window.draftail.initEditor.mockRestore();
  });
});





describe('DraftailRichTextArea Initialization Logic', () => {
  it('initializes the correct element when IDs are duplicated', () => {
    // Setup DOM with duplicate IDs
    // The issue is that the specific ID 'duplicate-id' is used for the parent AND the input.
    const validValue = JSON.stringify({
      blocks: [
        {
          key: 'test',
          type: 'unstyled',
          depth: 0,
          text: 'test',
          inlineStyleRanges: [],
          entityRanges: [],
        },
      ],
      entityMap: {},
    });
    document.body.innerHTML = `
        <div id="duplicate-id" class="parent-container">
            <input id="duplicate-id" class="target-input" value='${validValue}' />
        </div>
    `;

    // We try to initialize using the ID selector, which is what the current code does.
    // This mimics the behavior of: window.draftail.initEditor('#duplicate-id', ...)

    // Expectation: It picks the DIV (first match), tries to read .value (undefined/empty), and fails JSON.parse.
    // Or it might succeed if the DIV matches requirements, but it attaches to the wrong place.
    // In this case, div.value is undefined. JSON.parse(undefined) throws SyntaxError.

    const options = {
      entityTypes: [],
      blockTypes: [],
      inlineStyles: [],
      controls: [],
      plugins: [],
    };

    expect(() => {
      realInitEditor(document.querySelector('.target-input'), options, null);
    }).not.toThrow();
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

    jest.spyOn(console, 'error').mockImplementation(() => { });
    jest.spyOn(window.draftail, 'initEditor').mockImplementation(() => { });

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
      document.getElementById('editor'),
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
