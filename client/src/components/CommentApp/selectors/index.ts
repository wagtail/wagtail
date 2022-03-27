import { createSelector } from 'reselect';
import type { Comment } from '../state/comments';
import type { State } from '../state';

export const selectComments = (state: State) => state.comments.comments;
export const selectFocused = (state: State) => state.comments.focusedComment;
export const selectRemoteCommentCount = (state: State) =>
  state.comments.remoteCommentCount;

export function selectCommentsForContentPathFactory(contentpath: string) {
  return createSelector(selectComments, (comments) =>
    [...comments.values()].filter(
      (comment: Comment) =>
        comment.contentpath === contentpath &&
        !(comment.deleted || comment.resolved),
    ),
  );
}

export function selectCommentFactory(localId: number) {
  return createSelector(selectComments, (comments) => {
    const comment = comments.get(localId);
    if (comment !== undefined && (comment.deleted || comment.resolved)) {
      return undefined;
    }
    return comment;
  });
}

export const selectEnabled = (state: State) => state.settings.commentsEnabled;

export const selectIsDirty = createSelector(
  selectComments,
  selectRemoteCommentCount,
  (comments, remoteCommentCount) => {
    if (remoteCommentCount !== comments.size) {
      return true;
    }
    return Array.from(comments.values()).some((comment) => {
      if (
        comment.deleted ||
        comment.resolved ||
        comment.replies.size !== comment.remoteReplyCount ||
        comment.originalText !== comment.text
      ) {
        return true;
      }
      return Array.from(comment.replies.values()).some(
        (reply) => reply.deleted || reply.originalText !== reply.text,
      );
    });
  },
);

export const selectCommentCount = (state: State) =>
  [...state.comments.comments.values()].filter(
    (comment: Comment) => !comment.deleted && !comment.resolved,
  ).length;
