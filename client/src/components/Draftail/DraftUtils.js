
  /**
  * Function returns collection of currently selected blocks.
  */
  const getSelectedBlocksList = (editorState) => {
    const selectionState = editorState.getSelection();
    const content = editorState.getCurrentContent();
    const startKey = selectionState.getStartKey();
    const endKey = selectionState.getEndKey();
    const blockMap = content.getBlockMap();
    const blocks =  blockMap
      .toSeq()
      .skipUntil((_, k) => k === startKey)
      .takeUntil((_, k) => k === endKey)
      .concat([[endKey, blockMap.get(endKey)]]);
    return blocks.toList();
  };

  /**
  * Function will return currently selected text in the editor.
  */
  export const getSelectionText = (editorState) => {
    let selectedText = '';
    const selection = editorState.getSelection();
    let start = selection.getAnchorOffset();
    let end = selection.getFocusOffset();
    const selectedBlocks = getSelectedBlocksList(editorState);

    if (selectedBlocks.size > 0) {
      if (selection.getIsBackward()) {
        const temp = start;
        start = end;
        end = temp;
      }

      for (let i = 0; i < selectedBlocks.size; i += 1) {
        const blockStart = i === 0 ? start : 0;
        const blockEnd = i === (selectedBlocks.size - 1) ? end : selectedBlocks.get(i).getText().length;
        selectedText += selectedBlocks.get(i).getText().slice(blockStart, blockEnd);
      }
    }
    return selectedText;
  };
