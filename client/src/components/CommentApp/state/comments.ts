import type { Annotation } from '../utils/annotation';
import * as actions from '../actions/comments';
import { update } from './utils';
import produce, { enableMapSet, enableES5 } from "immer";

enableES5()
enableMapSet()

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
  text: string;
  newText: string;
  deleted: boolean;
}

export interface NewReplyOptions {
  remoteId?: number | null;
  mode?: CommentReplyMode;
  text?: string;
}

export function newCommentReply(
  localId: number,
  author: Author | null,
  date: number,
  {
    remoteId = null,
    mode = 'default',
    text = '',
  }: NewReplyOptions
): CommentReply {
  return {
    localId,
    remoteId,
    mode,
    author,
    date,
    text,
    newText: '',
    deleted: false,
  };
}

export type CommentReplyUpdate = Partial<CommentReply>;

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
  author: Author | null;
  date: number;
  text: string;
  replies: Map<number, CommentReply>;
  newReply: string;
  newText: string;
  remoteReplyCount: number;
}

export interface NewCommentOptions {
  remoteId?: number | null;
  mode?: CommentMode;
  text?: string;
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
    replies = new Map(),
  }: NewCommentOptions
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
    replies,
    newReply: '',
    newText: '',
    deleted: false,
    remoteReplyCount: Array.from(replies.values()).reduce(
      (n, reply) => (reply.remoteId !== null ? n + 1 : n),
      0
    ),
  };
}

export type CommentUpdate = Partial<Comment>;

export interface CommentsState {
  comments: Map<number, Comment>;
  focusedComment: number | null;
  pinnedComment: number | null;
  remoteCommentCount: number; // This is redundant, but stored for efficiency as it will change only as the app adds its loaded comments
}

const INITIAL_STATE: CommentsState = {
  comments: new Map(),
  focusedComment: null,
  pinnedComment: null,
  remoteCommentCount: 0,
};

export const reducer = produce((draft: CommentsState, action: actions.Action) => {
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
        update(comment, action.update)
      }
      break;
    }
    case actions.DELETE_COMMENT: {
      const comment = draft.comments.get(action.commentId);
      if (!comment) {
        break
      } else if (!comment.remoteId) {
        // If the comment doesn't exist in the database, there's no need to keep it around locally
        draft.comments.delete(action.commentId);
      } else {
        comment.deleted = true;
      }

      // Unset focusedComment if the focused comment is the one being deleted
      if (draft.focusedComment === action.commentId) {
        draft.focusedComment = null;
      }
      if (draft.pinnedComment === action.commentId) {
        draft.pinnedComment = null;
      }
      break;
    }
    case actions.SET_FOCUSED_COMMENT: {
      if ((action.commentId === null) || (draft.comments.has(action.commentId))) {
        draft.focusedComment = action.commentId;
        if (action.updatePinnedComment) {
          draft.pinnedComment = action.commentId;
        }
      }
      break;
    }
    case actions.ADD_REPLY: {
      const comment = draft.comments.get(action.commentId);
      if (!comment) {
        break
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
      update(reply, action.update)
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
  }
}, INITIAL_STATE)
