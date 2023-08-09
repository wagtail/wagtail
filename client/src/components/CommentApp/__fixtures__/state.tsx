import type { Comment, CommentReply, CommentsState } from '../state/comments';

const remoteReply: CommentReply = {
  localId: 2,
  remoteId: 2,
  mode: 'default',
  author: { id: 1, name: 'test user' },
  date: 0,
  text: 'a reply',
  originalText: 'a reply',
  newText: '',
  deleted: false,
};

const localReply: CommentReply = {
  localId: 3,
  remoteId: null,
  mode: 'default',
  author: { id: 1, name: 'test user' },
  date: 0,
  text: 'another reply',
  originalText: 'another new reply',
  newText: '',
  deleted: false,
};

const remoteComment: Comment = {
  contentpath: 'test_contentpath',
  position: '',
  localId: 1,
  annotation: null,
  remoteId: 1,
  mode: 'default',
  deleted: false,
  resolved: false,
  author: { id: 1, name: 'test user' },
  date: 0,
  text: 'test text',
  originalText: 'test text',
  newReply: '',
  newText: '',
  remoteReplyCount: 1,
  replies: new Map([
    [remoteReply.localId, remoteReply],
    [localReply.localId, localReply],
  ]),
};

const localComment: Comment = {
  contentpath: 'test_contentpath_2',
  position: '',
  localId: 4,
  annotation: null,
  remoteId: null,
  mode: 'default',
  deleted: false,
  resolved: false,
  author: { id: 1, name: 'test user' },
  date: 0,
  text: 'unsaved comment',
  originalText: 'unsaved comment',
  newReply: '',
  newText: '',
  replies: new Map(),
  remoteReplyCount: 0,
};

export const basicCommentsState: CommentsState = {
  focusedComment: 1,
  forceFocus: false,
  pinnedComment: 1,
  remoteCommentCount: 1,
  comments: new Map([
    [remoteComment.localId, remoteComment],
    [localComment.localId, localComment],
  ]),
};
