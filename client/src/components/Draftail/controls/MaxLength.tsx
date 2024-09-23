import React from 'react';
import { ControlComponentProps, BLOCK_TYPE } from 'draftail';

import { ContentBlock, EditorState } from 'draft-js';
import { gettext } from '../../../utils/gettext';

/**
 * Count characters in a string, with special processing to account for astral symbols in UCS-2,
 * matching the behaviour of HTML-native maxlength. See:
 * - https://mathiasbynens.be/notes/javascript-unicode
 * - https://github.com/RadLikeWhoa/Countable/blob/master/Countable.js#L29
 */
export const countCharacters = (text: string) => {
  if (text) {
    // Flags: return all matches (g), matching newlines as characters (s), as unicode code points (u).
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions#advanced_searching_with_flags.
    const matches = text.match(/./gsu);
    return matches ? matches.length : 0;
  }

  return 0;
};

/**
 * Retrieves the plain text content of the editor similarly of how we would server-side,
 * ignoring inline formatting, atomic blocks, and discarding line breaks.
 */
export const getPlainText = (editorState: EditorState) => {
  const content = editorState.getCurrentContent();
  const text = content.getBlockMap().reduce<string>((acc, item) => {
    const block = item as ContentBlock;
    const isAtomicBlock = block.getType() === BLOCK_TYPE.ATOMIC;

    return `${acc}${isAtomicBlock ? '' : block.getText()}`;
  }, '');

  return text.replace(/\n/g, '');
};

interface MaxLengthProps extends ControlComponentProps {
  maxLength: number;
  id: string;
}

/**
 * Shows the editor’s character count, with a calculation of unicode characters
 * matching that of `maxlength` attributes.
 */
const MaxLength = ({ getEditorState, maxLength, id }: MaxLengthProps) => {
  const text = getPlainText(getEditorState());

  return (
    <div className="w-inline-block w-tabular-nums w-help-text" id={id}>
      <span className="w-sr-only">{gettext('Character count:')}</span>
      <span>{`${countCharacters(text)}/${maxLength}`}</span>
    </div>
  );
};

export default MaxLength;
