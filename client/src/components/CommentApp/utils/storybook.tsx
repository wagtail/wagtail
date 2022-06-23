import React from 'react';

import { Store } from '../state';
import { addComment, setFocusedComment, addReply } from '../actions/comments';
import {
  Author,
  Comment,
  NewCommentOptions,
  newComment,
  newCommentReply,
  NewReplyOptions,
} from '../state/comments';
import { LayoutController } from './layout';
import { getNextCommentId } from './sequences';

import CommentComponent from '../components/Comment/index';

export function RenderCommentsForStorybook({
  store,
  author,
}: {
  store: Store;
  author?: Author;
}) {
  const [state, setState] = React.useState(store.getState());
  store.subscribe(() => {
    setState(store.getState());
  });

  const layout = new LayoutController();

  const commentsToRender: Comment[] = Array.from(
    state.comments.comments.values(),
  );

  const commentsRendered = commentsToRender.map((comment) => (
    <CommentComponent
      key={comment.localId}
      store={store}
      layout={layout}
      user={
        author || {
          id: 1,
          name: 'Admin',
          avatarUrl:
            'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
        }
      }
      comment={comment}
      isVisible={true}
      isFocused={comment.localId === state.comments.focusedComment}
    />
  ));

  return <ol className="comments-list">{commentsRendered}</ol>;
}

interface AddTestCommentOptions extends NewCommentOptions {
  focused?: boolean;
  author?: Author;
}

export function addTestComment(
  store: Store,
  options: AddTestCommentOptions,
): number {
  const commentId = getNextCommentId();

  const addCommentOptions = options;

  const author = options.author || {
    id: 1,
    name: 'Admin',
    avatarUrl:
      'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
  };

  // We must have a remoteId unless the comment is being created
  if (options.mode !== 'creating' && options.remoteId === undefined) {
    addCommentOptions.remoteId = commentId;
  }

  // Comment must be focused if the mode is anything other than default
  if (options.mode !== 'default' && options.focused === undefined) {
    addCommentOptions.focused = true;
  }

  store.dispatch(
    addComment(
      newComment(
        'test',
        '',
        commentId,
        null,
        author,
        Date.now(),
        addCommentOptions,
      ),
    ),
  );

  if (options.focused) {
    store.dispatch(setFocusedComment(commentId, { updatePinnedComment: true }));
  }

  return commentId;
}

interface AddTestReplyOptions extends NewReplyOptions {
  focused?: boolean;
  author?: Author;
}

export function addTestReply(
  store: Store,
  commentId: number,
  options: AddTestReplyOptions,
) {
  const addReplyOptions = options;
  const author = options.author || {
    id: 1,
    name: 'Admin',
    avatarUrl:
      'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
  };

  if (!options.remoteId) {
    addReplyOptions.remoteId = 1;
  }

  store.dispatch(
    addReply(
      commentId,
      newCommentReply(1, author, Date.now(), addReplyOptions),
    ),
  );
}
