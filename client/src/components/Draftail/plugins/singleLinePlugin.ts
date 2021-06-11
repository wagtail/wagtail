import { ContentBlock, ContentState, EditorState, genKey } from 'draft-js';

/**
 * Condense an array of content blocks into a single block.
 */
export function condenseBlocks(editorState: EditorState) {
  const blocks = editorState.getCurrentContent().getBlocksAsArray();

  if (blocks.length < 2) {
    return editorState;
  }

  let text = '';
  let characterList;

  // Gather all the text/characterList and concat them
  blocks.forEach((block) => {
    // Atomic blocks should be ignored (stripped)
    if (block.getType() !== 'atomic') {
      text += block.getText();
      characterList = characterList
        ? characterList.concat(block.getCharacterList())
        : block.getCharacterList().slice();
    }
  });

  const contentBlock = new ContentBlock({
    key: genKey(),
    type: 'unstyled',
    depth: 0,
    text,
    characterList,
  });

  // Update the editor state with the compressed version.
  const newContentState = ContentState.createFromBlockArray([contentBlock]);
  // Create the new state as an undo-able action.
  const nextState = EditorState.push(
    editorState,
    newContentState,
    'remove-range',
  );
  // Move the selection to the end.
  return EditorState.moveFocusToEnd(nextState);
}

const singleLinePlugin = () => ({
  onChange(editorState: EditorState) {
    return condenseBlocks(editorState);
  },

  /**
   * Handle return key without doing anything.
   */
  handleReturn() {
    return 'handled';
  },
});

export default singleLinePlugin;
