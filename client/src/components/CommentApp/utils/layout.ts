import type { Annotation } from './annotation';
import { getOrDefault } from './maps';

const GAP = 20.0; // Gap between comments in pixels
const TOP_MARGIN = 100.0; // Spacing from the top to the first comment in pixels
const OFFSET = -50; // How many pixels from the annotation position should the comments be placed?

export class LayoutController {
  commentElements: Map<number, HTMLElement> = new Map();
  commentAnnotations: Map<number, Annotation> = new Map();
  commentTabs: Map<number, string | null> = new Map();
  commentDesiredPositions: Map<number, number> = new Map();
  commentHeights: Map<number, number> = new Map();
  pinnedComment: number | null = null;
  commentCalculatedPositions: Map<number, number> = new Map();
  isDirty = false;

  setCommentElement(commentId: number, element: HTMLElement | null) {
    if (element !== null) {
      this.commentElements.set(commentId, element);
    } else {
      this.commentElements.delete(commentId);
    }

    this.isDirty = true;
  }

  setCommentAnnotation(commentId: number, annotation: Annotation) {
    this.commentAnnotations.set(commentId, annotation);
    this.commentTabs.set(commentId, annotation.getTab() || null);
    this.updateDesiredPosition(commentId);
    this.isDirty = true;
  }

  setCommentHeight(commentId: number, height: number) {
    if (this.commentHeights.get(commentId) !== height) {
      this.commentHeights.set(commentId, height);
      this.isDirty = true;
    }
  }

  setPinnedComment(commentId: number | null) {
    this.pinnedComment = commentId;
    this.isDirty = true;
  }

  updateDesiredPosition(commentId: number) {
    const annotation = this.commentAnnotations.get(commentId);

    if (!annotation) {
      return;
    }

    this.commentDesiredPositions.set(
      commentId,
      annotation.getDesiredPosition(commentId === this.pinnedComment) + OFFSET
    );
  }

  refreshDesiredPositions() {
    this.commentAnnotations.forEach((_, commentId) =>
      this.updateDesiredPosition(commentId)
    );
  }

  refresh() {
    const oldDesiredPositions = new Map(this.commentDesiredPositions);
    this.refreshDesiredPositions();
    // It's not great to be recalculating all positions so regularly, but Wagtail's FE widgets
    // aren't very constrained so could change layout in any number of ways. If we have a stable FE
    // widget framework in the future, this could be used to trigger the position refresh more
    // intelligently, or alternatively once comments is incorporated into the page form, a
    // MutationObserver could potentially track most types of changes.
    if (this.commentDesiredPositions !== oldDesiredPositions) {
      this.isDirty = true;
    }

    if (!this.isDirty) {
      return false;
    }

    interface Block {
      position: number;
      height: number;
      comments: number[];
      containsPinnedComment: boolean;
      pinnedCommentPosition: number;
    }

    // Build list of blocks (starting with one for each comment)
    let blocks: Block[] = Array.from(this.commentElements.keys()).map(
      (commentId) => ({
        position: getOrDefault(this.commentDesiredPositions, commentId, 0),
        height: getOrDefault(this.commentHeights, commentId, 0),
        comments: [commentId],
        containsPinnedComment:
            this.pinnedComment !== null && commentId === this.pinnedComment,
        pinnedCommentPosition: 0,
      })
    );

    // Sort blocks
    blocks.sort(
      (block, comparisonBlock) => block.position - comparisonBlock.position
    );

    // Resolve overlapping blocks
    let overlaps = true;
    while (overlaps) {
      overlaps = false;
      const newBlocks: Block[] = [];
      let previousBlock: Block | null = null;
      const pinnedCommentPosition = this.pinnedComment ?
        this.commentDesiredPositions.get(this.pinnedComment) : undefined;

      for (const block of blocks) {
        if (previousBlock) {
          if (
            previousBlock.position + previousBlock.height + GAP >
            block.position
          ) {
            overlaps = true;

            // Merge the blocks
            previousBlock.comments.push(...block.comments);

            if (block.containsPinnedComment) {
              previousBlock.containsPinnedComment = true;
              previousBlock.pinnedCommentPosition =
                block.pinnedCommentPosition + previousBlock.height;
            }
            previousBlock.height += block.height;

            // Make sure comments don't disappear off the top of the page
            // But only if a comment isn't focused
            if (
              !this.pinnedComment &&
              previousBlock.position < TOP_MARGIN + OFFSET
            ) {
              previousBlock.position =
                TOP_MARGIN + previousBlock.height - OFFSET;
            }

            // If this block contains the focused comment, position it so
            // the focused comment is in it's desired position
            if (
              pinnedCommentPosition &&
              previousBlock.containsPinnedComment
            ) {
              previousBlock.position =
                pinnedCommentPosition -
                previousBlock.pinnedCommentPosition;
            }

            continue;
          }
        }

        newBlocks.push(block);
        previousBlock = block;
      }

      blocks = newBlocks;
    }

    // Write positions
    blocks.forEach((block) => {
      let currentPosition = block.position;
      block.comments.forEach((commentId) => {
        this.commentCalculatedPositions.set(commentId, currentPosition);
        const height = this.commentHeights.get(commentId);
        if (height) {
          currentPosition += height + GAP;
        }
      });
    });

    this.isDirty = false;

    return true;
  }

  getCommentVisible(tab: string | null, commentId: number): boolean {
    const commentTab = getOrDefault(this.commentTabs, commentId, null);
    return commentTab === tab;
  }

  getCommentPosition(commentId: number) {
    if (this.commentCalculatedPositions.has(commentId)) {
      return this.commentCalculatedPositions.get(commentId);
    }
    return this.commentDesiredPositions.get(commentId);
  }
}
