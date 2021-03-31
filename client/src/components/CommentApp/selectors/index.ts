import { createSelector } from 'reselect';
import type { Comment } from '../state/comments';
import type { State } from '../state';

export const selectComments = (state: State) => state.comments.comments;
export const selectFocused = (state: State) => state.comments.focusedComment;

export function selectCommentsForContentPathFactory(contentpath: string) {
  return createSelector(selectComments, (comments) =>
    [...comments.values()].filter(
      (comment: Comment) =>
        comment.contentpath === contentpath && !comment.deleted
    )
  );
}

export function selectCommentFactory(localId: number) {
  return createSelector(selectComments, (comments) => {
    const comment = comments.get(localId);
    if (comment !== undefined && comment.deleted) {
      return undefined
    }
    return comment
  }

  );
}

export const selectEnabled = (state: State) => state.settings.commentsEnabled;