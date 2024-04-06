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

  it.only('should support creating a new editor with event dispatching', async () => {
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
    /* eslint-enable no-console */
  });
});
