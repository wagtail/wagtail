import React from 'react';
import ReactDOM from 'react-dom';
import { createStore } from 'redux';

import type { Annotation } from './utils/annotation';
import { LayoutController } from './utils/layout';
import { getOrDefault } from './utils/maps';
import { getNextCommentId, getNextReplyId } from './utils/sequences';
import { Store, reducer } from './state';
import { Comment, newCommentReply, newComment, Author } from './state/comments';
import {
  addComment,
  addReply,
  setFocusedComment,
  updateComment,
  commentActionFunctions
} from './actions/comments';
import { updateGlobalSettings } from './actions/settings';
import {
  selectComments,
  selectCommentsForContentPathFactory,
  selectCommentFactory,
  selectEnabled,
  selectFocused,
  selectIsDirty
} from './selectors';
import CommentComponent from './components/Comment';
import { CommentFormSetComponent } from './components/Form';
import { INITIAL_STATE as INITIAL_SETTINGS_STATE } from './state/settings';

export interface TranslatableStrings {
  COMMENT: string;
  SAVE: string;
  SAVING: string;
  CANCEL: string;
  DELETE: string;
  DELETING: string;
  SHOW_COMMENTS: string;
  EDIT: string;
  REPLY: string;
  RESOLVE: string;
  RETRY: string;
  DELETE_ERROR: string;
  CONFIRM_DELETE_COMMENT: string;
  SAVE_ERROR: string;
  MORE_ACTIONS: string;
}

export const defaultStrings = {
  COMMENT: 'Comment',
  SAVE: 'Save',
  SAVING: 'Saving...',
  CANCEL: 'Cancel',
  DELETE: 'Delete',
  DELETING: 'Deleting...',
  SHOW_COMMENTS: 'Show comments',
  EDIT: 'Edit',
  REPLY: 'Reply',
  RESOLVE: 'Resolve',
  RETRY: 'Retry',
  DELETE_ERROR: 'Delete error',
  CONFIRM_DELETE_COMMENT: 'Are you sure?',
  SAVE_ERROR: 'Save error',
  MORE_ACTIONS: 'More actions',
};

/* eslint-disable camelcase */
// This is done as this is serialized pretty directly from the Django model
export interface InitialCommentReply {
  pk: number;
  user: any;
  text: string;
  created_at: string;
  updated_at: string;
  deleted: boolean;
}

export interface InitialComment {
  pk: number;
  user: any;
  text: string;
  created_at: string;
  updated_at: string;
  replies: InitialCommentReply[];
  contentpath: string;
  position: string;
  deleted: boolean;
  resolved: boolean;
}
/* eslint-enable */

// eslint-disable-next-line camelcase
const getAuthor = (authors: Map<string, {name: string, avatar_url: string}>, id: any): Author => {
  const authorData = getOrDefault(authors, String(id), { name: '', avatar_url: '' });

  return {
    id,
    name: authorData.name,
    avatarUrl: authorData.avatar_url,
  };
};

function renderCommentsUi(
  store: Store,
  layout: LayoutController,
  comments: Comment[],
  strings: TranslatableStrings
): React.ReactElement {
  const state = store.getState();
  const { commentsEnabled, user } = state.settings;
  const focusedComment = state.comments.focusedComment;
  let commentsToRender = comments;

  if (!commentsEnabled || !user) {
    commentsToRender = [];
  }
  // Hide all resolved/deleted comments
  commentsToRender = commentsToRender.filter(({ deleted, resolved }) => !(deleted || resolved));
  const commentsRendered = commentsToRender.map((comment) => (
    <CommentComponent
      key={comment.localId}
      store={store}
      layout={layout}
      user={user}
      comment={comment}
      isFocused={comment.localId === focusedComment}
      strings={strings}
    />
  ));
  return (
    <ol className="comments-list">{commentsRendered}</ol>
  );
  /* eslint-enable react/no-danger */
}

export class CommentApp {
  store: Store;
  layout: LayoutController;
  utils = {
    selectCommentsForContentPathFactory,
    selectCommentFactory
  }
  selectors = {
    selectComments,
    selectEnabled,
    selectFocused,
    selectIsDirty
  }
  actions = commentActionFunctions;

  constructor() {
    this.store = createStore(reducer, {
      settings: INITIAL_SETTINGS_STATE
    });
    this.layout = new LayoutController();
  }
  // eslint-disable-next-line camelcase
  setUser(userId: any, authors: Map<string, {name: string, avatar_url: string}>) {
    this.store.dispatch(
      updateGlobalSettings({
        user: getAuthor(authors, userId)
      })
    );
  }
  updateAnnotation(
    annotation: Annotation,
    commentId: number
  ) {
    this.attachAnnotationLayout(annotation, commentId);
    this.store.dispatch(
      updateComment(
        commentId,
        { annotation: annotation }
      )
    );
  }
  attachAnnotationLayout(
    annotation: Annotation,
    commentId: number
  ) {
    // Attach an annotation to an existing comment in the layout

    // const layout engine know the annotation so it would position the comment correctly
    this.layout.setCommentAnnotation(commentId, annotation);
  }
  makeComment(annotation: Annotation, contentpath: string, position = '') {
    const commentId = getNextCommentId();

    this.attachAnnotationLayout(annotation, commentId);

    // Create the comment
    this.store.dispatch(
      addComment(
        newComment(
          contentpath,
          position,
          commentId,
          annotation,
          this.store.getState().settings.user,
          Date.now(),
          {
            mode: 'creating',
          }
        )
      )
    );

    // Focus and pin the comment
    this.store.dispatch(setFocusedComment(commentId, { updatePinnedComment: true }));
    return commentId;
  }
  renderApp(
    element: HTMLElement,
    outputElement: HTMLElement,
    userId: any,
    initialComments: InitialComment[],
    // eslint-disable-next-line camelcase
    authors: Map<string, {name: string, avatar_url: string}>,
    translationStrings: TranslatableStrings | null
  ) {
    let pinnedComment: number | null = null;
    this.setUser(userId, authors);

    const strings = translationStrings || defaultStrings;

    // Check if there is "comment" query parameter.
    // If this is set, the user has clicked on a "View on frontend" link of an
    // individual comment. We should focus this comment and scroll to it
    const urlParams = new URLSearchParams(window.location.search);
    let initialFocusedCommentId: number | null = null;
    const commentParams = urlParams.get('comment');
    if (commentParams) {
      initialFocusedCommentId = parseInt(commentParams, 10);
    }

    const render = () => {
      const state = this.store.getState();
      const commentList: Comment[] = Array.from(state.comments.comments.values());

      ReactDOM.render(
        <CommentFormSetComponent
          comments={commentList}
          remoteCommentCount={state.comments.remoteCommentCount}
        />,
        outputElement
      );

      // Check if the pinned comment has changed
      if (state.comments.pinnedComment !== pinnedComment) {
        // Tell layout controller about the pinned comment
        // so it is moved alongside its annotation
        this.layout.setPinnedComment(state.comments.pinnedComment);

        pinnedComment = state.comments.pinnedComment;
      }

      ReactDOM.render(
        renderCommentsUi(this.store, this.layout, commentList, strings),
        element,
        () => {
          // Render again if layout has changed (eg, a comment was added, deleted or resized)
          // This will just update the "top" style attributes in the comments to get them to move
          if (this.layout.refresh()) {
            ReactDOM.render(
              renderCommentsUi(this.store, this.layout, commentList, strings),
              element
            );
          }
        }
      );
    };

    // Fetch existing comments
    for (const comment of initialComments) {
      const commentId = getNextCommentId();

      // Create comment
      this.store.dispatch(
        addComment(
          newComment(
            comment.contentpath,
            comment.position,
            commentId,
            null,
            getAuthor(authors, comment.user),
            Date.parse(comment.created_at),
            {
              remoteId: comment.pk,
              text: comment.text,
              deleted: comment.deleted,
              resolved: comment.resolved
            }
          )
        )
      );

      // Create replies
      for (const reply of comment.replies) {
        this.store.dispatch(
          addReply(
            commentId,
            newCommentReply(
              getNextReplyId(),
              getAuthor(authors, reply.user),
              Date.parse(reply.created_at),
              {
                remoteId: reply.pk,
                text: reply.text,
                deleted: reply.deleted
              }
            )
          )
        );
      }

      // If this is the initial focused comment. Focus and pin it
      // TODO: Scroll to this comment
      if (initialFocusedCommentId && comment.pk === initialFocusedCommentId) {
        this.store.dispatch(setFocusedComment(commentId, { updatePinnedComment: true }));
      }
    }

    render();

    this.store.subscribe(render);

    // Unfocus when document body is clicked
    document.body.addEventListener('click', (e) => {
      if (e.target instanceof HTMLElement) {
        // ignore if click target is a comment or an annotation
        if (!e.target.closest('#comments, [data-annotation]')) {
          // Running store.dispatch directly here seems to prevent the event from being handled anywhere else
          setTimeout(() => {
            this.store.dispatch(setFocusedComment(null, { updatePinnedComment: true }));
          }, 1);
        }
      }
    });
  }
}

export function initCommentApp() {
  return new CommentApp();
}
