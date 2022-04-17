import { EditorState, convertFromRaw } from 'draft-js';

import { getSelectionText } from './DraftUtils';

describe('DraftUtils', () => {
  describe('#getSelectionText', () => {
    it('works', () => {
      const content = convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test1234',
          },
        ],
      });
      let editorState = EditorState.createWithContent(content);

      let selection = editorState.getSelection();
      selection = selection.merge({
        anchorOffset: 0,
        focusOffset: 4,
      });

      editorState = EditorState.acceptSelection(editorState, selection);

      expect(getSelectionText(editorState)).toBe('test');
    });

    it('empty', () => {
      expect(getSelectionText(EditorState.createEmpty())).toBe('');
    });

    it('backwards', () => {
      const content = convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test1234',
          },
        ],
      });
      let editorState = EditorState.createWithContent(content);

      let selection = editorState.getSelection();
      selection = selection.merge({
        anchorOffset: 8,
        focusOffset: 4,
        isBackward: true,
      });

      editorState = EditorState.acceptSelection(editorState, selection);

      expect(getSelectionText(editorState)).toBe('1234');
    });

    it('multiblock', () => {
      const content = convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test1234',
          },
          {
            key: 'b',
            text: 'multiblock',
          },
        ],
      });
      let editorState = EditorState.createWithContent(content);

      let selection = editorState.getSelection();
      selection = selection.merge({
        anchorKey: 'a',
        focusKey: 'b',
        anchorOffset: 4,
        focusOffset: 5,
        isBackward: false,
      });

      editorState = EditorState.acceptSelection(editorState, selection);

      expect(getSelectionText(editorState)).toBe('1234multi');
    });

    it('multiblock-backwards', () => {
      const content = convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test1234',
          },
          {
            key: 'b',
            text: 'multiblock',
          },
        ],
      });
      let editorState = EditorState.createWithContent(content);

      let selection = editorState.getSelection();
      selection = selection.merge({
        focusKey: 'a',
        anchorKey: 'b',
        anchorOffset: 5,
        focusOffset: 4,
        isBackward: true,
      });

      editorState = EditorState.acceptSelection(editorState, selection);

      expect(getSelectionText(editorState)).toBe('1234multi');
    });
  });
});
