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
