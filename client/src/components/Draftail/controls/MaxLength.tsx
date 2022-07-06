import React from 'react';
import { ControlComponentProps } from 'draftail';

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
 * Shows the editor’s character count, with a calculation of unicode characters
 * matching that of `maxlength` attributes.
 */
const MaxLength = ({ getEditorState }: ControlComponentProps) => {
  const editorState = getEditorState();
  const content = editorState.getCurrentContent();
  const text = content.getPlainText();

  return (
    <div className="w-inline-block w-tabular-nums w-label-3">
      <span className="w-sr-only">{gettext('Character count:')}</span>
      <span>{countCharacters(text)}</span>
    </div>
  );
};

export default MaxLength;
