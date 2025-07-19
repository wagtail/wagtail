import { DraftUtils } from 'draftail';
import { splitState } from '../CommentableEditor/CommentableEditor';

/**
 * Definition for a command in the Draftail context menu that inserts a block.
 *
 * @param {BoundDraftailWidget} widget - the bound Draftail widget
 * @param {object} blockDef - block definition for the block to be inserted
 * @param {object} addSibling - capability descriptors from the containing block's capabilities definition
 * @param {object} split - capability descriptor from the containing block's capabilities definition
 */
export class DraftailInsertBlockCommand {
  constructor(widget, blockDef, addSibling, split) {
    this.widget = widget;
    this.blockDef = blockDef;
    this.addSibling = addSibling;
    this.split = split;

    this.blockMax = addSibling.getBlockMax(blockDef.name);
    this.icon = blockDef.meta.icon;
    this.label = blockDef.meta.label;
    this.type = blockDef.name;
    this.blockDefId = blockDef.meta.blockDefId;
    this.isPreviewable = blockDef.meta.isPreviewable;
    this.description = blockDef.meta.description;
  }

  render({ option }) {
    // If the specific block has a limit, render the current number/max alongside the description
    const limitText =
      typeof blockMax === 'number'
        ? ` (${this.addSibling.getBlockCount(this.blockDef.name)}/${
            this.blockMax
          })`
        : '';
    return `${option.label}${limitText}`;
  }

  onSelect({ editorState }) {
    const result = splitState(
      DraftUtils.removeCommandPalettePrompt(editorState),
    );
    if (result.stateAfter.getCurrentContent().hasText()) {
      // There is content after the insertion point, so need to split the existing block.
      // Run the split after a timeout to circumvent potential race condition.
      setTimeout(() => {
        if (result) {
          this.split.fn(
            result.stateBefore,
            result.stateAfter,
            result.shouldMoveCommentFn,
          );
        }
        // setTimeout required to stop Draftail from giving itself focus again
        setTimeout(() => {
          this.addSibling.fn({ type: this.blockDef.name });
        }, 20);
      }, 50);
    } else {
      // Set the current block's content to the 'before' state, to remove the '/' separator and
      // reset the editor state (closing the context menu)
      this.widget.setState(result.stateBefore);
      // setTimeout required to stop Draftail from giving itself focus again
      setTimeout(() => {
        this.addSibling.fn({ type: this.blockDef.name });
      }, 20);
    }
  }
}
