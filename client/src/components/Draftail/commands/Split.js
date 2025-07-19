import { DraftUtils } from 'draftail';
import { splitState } from '../CommentableEditor/CommentableEditor';
import { gettext } from '../../../utils/gettext';

/**
 * Definition for a command in the Draftail context menu that inserts a block.
 *
 * @param {BoundDraftailWidget} widget - the bound Draftail widget
 * @param {object} split - capability descriptor from the containing block's capabilities definition
 */
export class DraftailSplitCommand {
  constructor(widget, split) {
    this.widget = widget;
    this.split = split;
    this.description = gettext('Split block');
  }

  icon = 'cut';
  type = 'split';

  onSelect({ editorState }) {
    const result = splitState(
      DraftUtils.removeCommandPalettePrompt(editorState),
    );
    // Run the split after a timeout to circumvent potential race condition.
    setTimeout(() => {
      if (result) {
        this.split.fn(
          result.stateBefore,
          result.stateAfter,
          result.shouldMoveCommentFn,
        );
      }
    }, 50);
  }
}
