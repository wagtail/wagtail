/**
 * Returns collection of currently selected blocks.
 * See https://github.com/jpuri/draftjs-utils/blob/e81c0ae19c3b0fdef7e0c1b70d924398956be126/js/block.js#L19.
 */
const getSelectedBlocksList = (editorState) => {
  const selectionState = editorState.getSelection();
  const content = editorState.getCurrentContent();
  const startKey = selectionState.getStartKey();
  const endKey = selectionState.getEndKey();
  const blockMap = content.getBlockMap();
  const blocks = blockMap
    .toSeq()
    .skipUntil((_, k) => k === startKey)
    .takeUntil((_, k) => k === endKey)
    .concat([[endKey, blockMap.get(endKey)]]);
  return blocks.toList();
};

/**
 * Returns the currently selected text in the editor.
 * See https://github.com/jpuri/draftjs-utils/blob/e81c0ae19c3b0fdef7e0c1b70d924398956be126/js/block.js#L106.
 */
export const getSelectionText = (editorState) => {
  const selection = editorState.getSelection();
  let start = selection.getAnchorOffset();
  let end = selection.getFocusOffset();
  const selectedBlocks = getSelectedBlocksList(editorState);

  if (selection.getIsBackward()) {
    const temp = start;
    start = end;
    end = temp;
  }

  let selectedText = '';
  for (let i = 0; i < selectedBlocks.size; i += 1) {
    const blockStart = i === 0 ? start : 0;
    const blockEnd =
      i === selectedBlocks.size - 1
        ? end
        : selectedBlocks.get(i).getText().length;
    selectedText += selectedBlocks.get(i).getText().slice(blockStart, blockEnd);
  }

  return selectedText;
};
