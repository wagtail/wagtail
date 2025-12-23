import React, { useCallback } from 'react';
import ReactDOM from 'react-dom';
import { legacy_createStore as createStore } from 'redux';

import type { Annotation } from './utils/annotation';
import { LayoutController } from './utils/layout';
import { getOrDefault } from './utils/maps';
import { getNextCommentId, getNextReplyId } from './utils/sequences';
import { Store, reducer } from './state';
import {
  Comment,
  newCommentReply,
  newComment,
  Author,
  INITIAL_STATE as INITIAL_COMMENTS_STATE,
} from './state/comments';
import { INITIAL_STATE as INITIAL_SETTINGS_STATE } from './state/settings';
import {
  addComment,
  addReply,
  setFocusedComment,
  updateComment,
  commentActionFunctions,
  invalidateContentPath,
} from './actions/comments';
import { updateGlobalSettings } from './actions/settings';
import {
  selectComments,
  selectCommentsForContentPathFactory,
  selectCommentFactory,
  selectFocused,
  selectIsDirty,
  selectCommentCount,
} from './selectors';
import CommentComponent from './components/Comment';
import { CommentFormSetComponent } from './components/Form';

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

const getAuthor = (
  authors: Map<string, { name: string; avatar_url: string }>,
  id: any,
): Author => {
  const authorData = getOrDefault(authors, String(id), {
    name: '',
    avatar_url: '',
  });

  return {
    id,
    name: authorData.name,
    avatarUrl: authorData.avatar_url,
  };
};

interface CommentListingProps {
  store: Store;
  layout: LayoutController;
  comments: Comment[];
}

function CommentListing({
  store,
  layout,
  comments,
}: CommentListingProps): React.ReactElement {
  const state = store.getState();
  const { user, currentTab } = state.settings;
  const { focusedComment, forceFocus } = state.comments;
  const commentsListRef = React.useRef<HTMLOListElement | null>(null);
  // Update the position of the comments listing as the window scrolls to keep the comments in line with the content
  const updateScroll = useCallback(
    (e: Event) => {
      if (!commentsListRef.current) {
        return;
      }

      if (
        e.type === 'scroll' &&
        !document.querySelector('.form-side--comments')
      ) {
        return;
      }

      const scrollContainer = document.querySelector('.content');
      const top = scrollContainer?.getBoundingClientRect().top;
      commentsListRef.current.style.top = `${top}px`;
    },
    [commentsListRef],
  );
  let commentsToRender = comments;

  React.useEffect(() => {
    const root = document.querySelector('#main');
    const commentSidePanel = document.querySelector(
      '[data-side-panel="comments"]',
    );

    root?.addEventListener('scroll', updateScroll);
    commentSidePanel?.addEventListener('show', updateScroll);

    return () => {
      root?.removeEventListener('scroll', updateScroll);
      commentSidePanel?.removeEventListener('show', updateScroll);
    };
  }, []);

  if (!user) {
    commentsToRender = [];
  }
  // Hide all resolved/deleted comments
  commentsToRender = commentsToRender.filter(
    ({ deleted, resolved }) => !(deleted || resolved),
  );
  const commentsRendered = commentsToRender.map((comment) => (
    <CommentComponent
      key={comment.localId}
      store={store}
      layout={layout}
      user={user}
      comment={comment}
      isFocused={comment.localId === focusedComment}
      forceFocus={forceFocus}
      isVisible={layout.getCommentVisible(currentTab, comment.localId)}
    />
  ));
  return (
    <ol ref={commentsListRef} className="comments-list">
      {commentsRendered}
    </ol>
  );
}

export class CommentApp {
  store: Store;

  layout: LayoutController;

  utils = {
    selectCommentsForContentPathFactory,
    selectCommentFactory,
  };

  selectors = {
    selectComments,
    selectFocused,
    selectIsDirty,
    selectCommentCount,
  };

  actions = commentActionFunctions;
  activationHandlers: (() => void)[] = [];

  constructor() {
    this.store = createStore(reducer, {
      comments: INITIAL_COMMENTS_STATE,
      settings: INITIAL_SETTINGS_STATE,
    } as any);
    this.layout = new LayoutController();
  }

  setUser(
    userId: any,
    authors: Map<string, { name: string; avatar_url: string }>,
  ) {
    this.store.dispatch(
      updateGlobalSettings({
        user: getAuthor(authors, userId),
      }),
    );
  }

  updateAnnotation(annotation: Annotation, commentId: number) {
    this.attachAnnotationLayout(annotation, commentId);
    this.store.dispatch(updateComment(commentId, { annotation: annotation }));
  }

  attachAnnotationLayout(annotation: Annotation, commentId: number) {
    // Attach an annotation to an existing comment in the layout

    // const layout engine know the annotation so it would position the comment correctly
    this.layout.setCommentAnnotation(commentId, annotation);
  }

  setCurrentTab(tab: string | null) {
    this.store.dispatch(updateGlobalSettings({ currentTab: tab }));
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
          },
        ),
      ),
    );

    // Focus and pin the comment
    this.store.dispatch(
      setFocusedComment(commentId, {
        updatePinnedComment: true,
        forceFocus: true,
      }),
    );
    return commentId;
  }

  activate() {
    this.activationHandlers.forEach((handler) => handler());
  }

  onActivate(handler: () => void) {
    this.activationHandlers.push(handler);
  }

  invalidateContentPath(contentPath: string) {
    // Called when a given content path on the form is no longer valid (eg, a block has been deleted)
    this.store.dispatch(invalidateContentPath(contentPath));
  }

  updateContentPath(commentId: number, newContentPath: string) {
    this.store.dispatch(
      updateComment(commentId, { contentpath: newContentPath }),
    );
  }

  renderApp(
    element: HTMLElement,
    outputElement: HTMLElement,
    userId: any,
    initialComments: InitialComment[],

    authors: Map<string, { name: string; avatar_url: string }>,
  ) {
    let pinnedComment: number | null = null;
    this.setUser(userId, authors);

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
      const commentList: Comment[] = Array.from(
        state.comments.comments.values(),
      );

      ReactDOM.render(
        <CommentFormSetComponent
          comments={commentList.filter(
            (comment) => comment.mode !== 'creating',
          )}
          remoteCommentCount={state.comments.remoteCommentCount}
        />,
        outputElement,
      );

      // Check if the pinned comment has changed
      if (state.comments.pinnedComment !== pinnedComment) {
        // Tell layout controller about the pinned comment
        // so it is moved alongside its annotation
        this.layout.setPinnedComment(state.comments.pinnedComment);

        pinnedComment = state.comments.pinnedComment;
      }

      ReactDOM.render(
        <CommentListing
          store={this.store}
          layout={this.layout}
          comments={commentList}
        />,
        element,
        () => {
          // Render again if layout has changed (eg, a comment was added, deleted or resized)
          // This will just update the "top" style attributes in the comments to get them to move
          this.layout.refreshDesiredPositions(state.settings.currentTab);
          if (this.layout.refreshLayout()) {
            ReactDOM.render(
              <CommentListing
                store={this.store}
                layout={this.layout}
                comments={commentList}
              />,
              element,
            );
          }
        },
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
              resolved: comment.resolved,
            },
          ),
        ),
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
                deleted: reply.deleted,
              },
            ),
          ),
        );
      }

      // If this is the initial focused comment. Focus and pin it

      // TODO: Scroll to this comment
      if (initialFocusedCommentId && comment.pk === initialFocusedCommentId) {
        this.store.dispatch(
          setFocusedComment(commentId, {
            updatePinnedComment: true,
            forceFocus: true,
          }),
        );
      }
    }

    render();

    this.store.subscribe(render);

    // Unfocus when document body is clicked
    document.body.addEventListener('mousedown', (e) => {
      if (e.target instanceof HTMLElement) {
        // ignore if click target is a comment or an annotation
        if (
          !e.target.closest('#comments, [data-annotation], [data-comment-add]')
        ) {
          // Running store.dispatch directly here seems to prevent the event from being handled anywhere else
          setTimeout(() => {
            this.store.dispatch(
              setFocusedComment(null, {
                updatePinnedComment: true,
                forceFocus: false,
              }),
            );
          }, 200);
        }
      }
    });

    document.body.addEventListener('commentAnchorVisibilityChange', () => {
      // If any streamfield blocks or panels have collapsed or expanded
      // check if we need to rerender
      this.layout.refreshDesiredPositions(
        this.store.getState().settings.currentTab,
      );
      if (this.layout.refreshLayout()) {
        render();
      }
    });
  }
}

export function initCommentApp() {
  return new CommentApp();
}
