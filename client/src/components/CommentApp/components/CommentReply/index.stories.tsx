import React from 'react';
import { createStore } from 'redux';

import { Store, reducer } from '../../state';

import {
  RenderCommentsForStorybook,
  addTestComment,
  addTestReply,
} from '../../utils/storybook';

export default { title: 'Commenting/Comment Reply' };

export function reply() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
  });

  addTestReply(store, commentId, {
    mode: 'default',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function replyFromSomeoneElse() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
  });

  addTestReply(store, commentId, {
    mode: 'default',
    text: 'An example reply',
    author: {
      id: 2,
      name: 'Someone else',
      avatarUrl:
        'https://gravatar.com/avatar/31c3d5cc27d1faa321c2413589e8a53f?s=200&d=robohash&r=x',
    },
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function focused() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'default',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function editing() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'editing',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function saving() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'saving',
    text: 'An example reply',
  });
  return <RenderCommentsForStorybook store={store} />;
}

export function saveError() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'save_error',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function deleteConfirm() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'delete_confirm',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function deleting() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'deleting',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function deleteError() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'delete_error',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}

export function deleted() {
  const store: Store = createStore(reducer);

  const commentId = addTestComment(store, {
    mode: 'default',
    text: 'An example comment',
    focused: true,
  });

  addTestReply(store, commentId, {
    mode: 'deleted',
    text: 'An example reply',
  });

  return <RenderCommentsForStorybook store={store} />;
}
