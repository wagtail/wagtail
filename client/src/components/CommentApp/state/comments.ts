import produce, { enableMapSet, enableES5 } from 'immer';
import type { Annotation } from '../utils/annotation';
import * as actions from '../actions/comments';
import { update } from './utils';

enableES5();
enableMapSet();

export interface Author {
  id: any;
  name: string;
  avatarUrl?: string;
}

export type CommentReplyMode =
  | 'default'
  | 'editing'
  | 'saving'
  | 'delete_confirm'
  | 'deleting'
  | 'deleted'
  | 'save_error'
  | 'delete_error';

export interface CommentReply {
  localId: number;
  remoteId: number | null;
  mode: CommentReplyMode;
  author: Author | null;
  date: number;
  deleted: boolean;
  // There are three variables used for text
  // text is the canonical text, that will be output to the form
  // newText stores the edited version of the text until it is saved
  // originalText stores the text upon reply creation, and is
  // used to check whether existing replies have been edited
  text: string;
  originalText: string;
  newText: string;
}

export interface NewReplyOptions {
  remoteId?: number | null;
  mode?: CommentReplyMode;
  text?: string;
  deleted?: boolean;
}

export function newCommentReply(
  localId: number,
  author: Author | null,
  date: number,
  {
    remoteId = null,
    mode = 'default',
    text = '',
    deleted = false,
  }: NewReplyOptions,
): CommentReply {
  return {
    localId,
    remoteId,
    mode,
    author,
    date,
    text,
    originalText: text,
    newText: '',
    deleted,
  };
}

export type CommentReplyUpdate = Partial<Omit<CommentReply, 'originalText'>>;

export type CommentMode =
  | 'default'
  | 'creating'
  | 'editing'
  | 'saving'
  | 'delete_confirm'
  | 'deleting'
  | 'deleted'
  | 'save_error'
  | 'delete_error';

export interface Comment {
  contentpath: string;
  localId: number;
  annotation: Annotation | null;
  position: string;
  remoteId: number | null;
  mode: CommentMode;
  deleted: boolean;
  resolved: boolean;
  author: Author | null;
  date: number;
  replies: Map<number, CommentReply>;
  newReply: string;
  remoteReplyCount: number;
  // There are three variables used for text
  // text is the canonical text, that will be output to the form
  // newText stores the edited version of the text until it is saved
  // originalText stores the text upon comment creation, and is
  // used to check whether existing comments have been edited
  text: string;
  originalText: string;
  newText: string;
}

export interface NewCommentOptions {
  remoteId?: number | null;
  mode?: CommentMode;
  text?: string;
  resolved?: boolean;
  deleted?: boolean;
  replies?: Map<number, CommentReply>;
}

export function newComment(
  contentpath: string,
  position: string,
  localId: number,
  annotation: Annotation | null,
  author: Author | null,
  date: number,
  {
    remoteId = null,
    mode = 'default',
    text = '',
    resolved = false,
    deleted = false,
    replies = new Map(),
  }: NewCommentOptions,
): Comment {
  return {
    contentpath,
    position,
    localId,
    annotation,
    remoteId,
    mode,
    author,
    date,
    text,
    originalText: text,
    replies,
    newReply: '',
    newText: '',
    deleted,
    resolved,
    remoteReplyCount: Array.from(replies.values()).reduce(
      (n, reply) => (reply.remoteId !== null ? n + 1 : n),
      0,
    ),
  };
}

export type CommentUpdate = Partial<Omit<Comment, 'originalText'>>;

export interface CommentsState {
  comments: Map<number, Comment>;
  forceFocus: boolean;
  focusedComment: number | null;
  pinnedComment: number | null;
  // This is redundant, but stored for efficiency as it will change only as the app adds its loaded comments
  remoteCommentCount: number;
}

export const INITIAL_STATE: CommentsState = {
  comments: new Map(),
  forceFocus: false,
  focusedComment: null,
  pinnedComment: null,
  remoteCommentCount: 0,
};

export const reducer = produce(
  (draft: CommentsState, action: actions.Action) => {
    /* eslint-disable no-param-reassign */
    const deleteComment = (comment: Comment) => {
      if (!comment.remoteId) {
        // If the comment doesn't exist in the database, there's no need to keep it around locally
        draft.comments.delete(comment.localId);
      } else {
        comment.deleted = true;
      }

      // Unset focusedComment if the focused comment is the one being deleted
      if (draft.focusedComment === comment.localId) {
        draft.focusedComment = null;
        draft.forceFocus = false;
      }
      if (draft.pinnedComment === comment.localId) {
        draft.pinnedComment = null;
      }
    };

    const resolveComment = (comment: Comment) => {
      if (!comment.remoteId) {
        // If the comment doesn't exist in the database, there's no need to keep it around locally
        draft.comments.delete(comment.localId);
      } else {
        comment.resolved = true;
      }
      // Unset focusedComment if the focused comment is the one being resolved
      if (draft.focusedComment === comment.localId) {
        draft.focusedComment = null;
      }
      if (draft.pinnedComment === comment.localId) {
        draft.pinnedComment = null;
      }
    };

    switch (action.type) {
      case actions.ADD_COMMENT: {
        draft.comments.set(action.comment.localId, action.comment);
        if (action.comment.remoteId) {
          draft.remoteCommentCount += 1;
        }
        break;
      }
      case actions.UPDATE_COMMENT: {
        const comment = draft.comments.get(action.commentId);
        if (comment) {
          if (action.update.newText && action.update.newText.length === 0) {
            break;
          }
          update(comment, action.update);
        }
        break;
      }
      case actions.DELETE_COMMENT: {
        const comment = draft.comments.get(action.commentId);
        if (!comment) {
          break;
        }

        deleteComment(comment);
        break;
      }
      case actions.RESOLVE_COMMENT: {
        const comment = draft.comments.get(action.commentId);
        if (!comment) {
          break;
        }

        resolveComment(comment);
        break;
      }
      case actions.SET_FOCUSED_COMMENT: {
        if (action.commentId === null || draft.comments.has(action.commentId)) {
          draft.focusedComment = action.commentId;
          if (action.updatePinnedComment) {
            draft.pinnedComment = action.commentId;
          }
          draft.forceFocus = action.forceFocus;
        }
        break;
      }
      case actions.ADD_REPLY: {
        const comment = draft.comments.get(action.commentId);
        if (!comment || action.reply.text.length === 0) {
          break;
        }
        if (action.reply.remoteId) {
          comment.remoteReplyCount += 1;
        }
        comment.replies.set(action.reply.localId, action.reply);
        break;
      }
      case actions.UPDATE_REPLY: {
        const comment = draft.comments.get(action.commentId);
        if (!comment) {
          break;
        }
        const reply = comment.replies.get(action.replyId);
        if (!reply) {
          break;
        }
        if (action.update.newText && action.update.newText.length === 0) {
          break;
        }
        update(reply, action.update);
        break;
      }
      case actions.DELETE_REPLY: {
        const comment = draft.comments.get(action.commentId);
        if (!comment) {
          break;
        }
        const reply = comment.replies.get(action.replyId);
        if (!reply) {
          break;
        }
        if (!reply.remoteId) {
          // The reply doesn't exist in the database, so we don't need to store it locally
          comment.replies.delete(reply.localId);
        } else {
          reply.deleted = true;
        }
        break;
      }
      case actions.INVALIDATE_CONTENT_PATH: {
        // Delete any comments that exist in the contentpath
        const comments = draft.comments;
        for (const comment of comments.values()) {
          if (comment.contentpath.startsWith(action.contentPath)) {
            resolveComment(comment);
          }
        }
        break;
      }
      default:
        break;
    }
  },
  INITIAL_STATE,
);
