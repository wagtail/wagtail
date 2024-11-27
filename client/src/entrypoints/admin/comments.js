import { gettext } from '../../utils/gettext';
import { initCommentApp } from '../../components/CommentApp/main';

const KEYCODE_M = 77;

/**
 * Entry point loaded when the comments system is in use.
 */
window.comments = (() => {
  const commentApp = initCommentApp();

  /**
   * Returns true if the provided keyboard event is using the 'add/focus comment' keyboard
   * shortcut
   */
  function isCommentShortcut(e) {
    return (e.ctrlKey || e.metaKey) && e.altKey && e.keyCode === KEYCODE_M;
  }

  function getContentPath(fieldNode) {
    // Return the total contentpath for an element as a string, in the form field.streamfield_uid.block...
    if (!fieldNode || fieldNode.closest('[data-contentpath-disabled]')) {
      return '';
    }
    let element = fieldNode.closest('[data-contentpath]');
    const contentpaths = [];
    while (element !== null) {
      contentpaths.push(element.dataset.contentpath);
      element = element.parentElement.closest('[data-contentpath]');
    }
    contentpaths.reverse();
    return contentpaths.join('.');
  }

  /**
   * Controls the positioning of a field level comment, and the display of the button
   * used to focus and pin the attached comment
   * `getAnchorNode` is called by the comments app to determine which node to
   * float the comment alongside
   */
  class BasicFieldLevelAnnotation {
    /**
     * Create a field-level annotation
     * @param {Element} fieldNode - an element to provide the comment position
     * @param {Element} node - the button to focus/pin the comment
     */
    constructor(fieldNode, node) {
      this.node = node;
      this.fieldNode = fieldNode;
      this.unsubscribe = null;
    }

    /**
     * Subscribes the annotation to update when the state of a particular comment changes,
     * and to focus that comment when clicked
     * @param {number} localId - the localId of the comment to subscribe to
     */
    subscribeToUpdates(localId) {
      const { selectFocused } = commentApp.selectors;
      const selectComment = commentApp.utils.selectCommentFactory(localId);
      const store = commentApp.store;
      const initialState = store.getState();
      let focused = selectFocused(initialState) === localId;
      if (focused) {
        this.onFocus();
      }
      this.show();
      this.unsubscribe = store.subscribe(() => {
        const state = store.getState();
        const comment = selectComment(state);
        if (!comment) {
          this.onDelete();
        }
        const nowFocused = selectFocused(state) === localId;
        if (nowFocused !== focused) {
          if (focused) {
            this.onUnfocus();
          } else {
            this.onFocus();
          }
          focused = nowFocused;
        }
      });
      this.setOnClickHandler(localId);
    }

    onDelete() {
      this.node.remove();
      if (this.unsubscribe) {
        this.unsubscribe();
      }
    }

    onFocus() {
      this.node.classList.add('w-field__comment-button--focused');
      this.node.ariaLabel = gettext('Unfocus comment');
    }

    onUnfocus() {
      this.node.classList.remove('w-field__comment-button--focused');
      this.node.ariaLabel = gettext('Focus comment');

      // TODO: ensure comment is focused accessibly when this is clicked,
      // and that screenreader users can return to the annotation point when desired
    }

    show() {
      this.node.classList.remove('!w-hidden');
    }

    hide() {
      this.node.classList.add('!w-hidden');
    }

    setOnClickHandler(localId) {
      this.node.addEventListener('click', () => {
        // Open the comments side panel
        commentApp.activate();

        commentApp.store.dispatch(
          commentApp.actions.setFocusedComment(localId, {
            updatePinnedComment: true,
            forceFocus: true,
          }),
        );
      });
    }

    getTab() {
      return this.fieldNode.closest('[role="tabpanel"]')?.getAttribute('id');
    }

    getAnchorNode() {
      return this.fieldNode;
    }
  }

  class MissingElementError extends Error {
    constructor(element, ...params) {
      super(...params);
      this.name = 'MissingElementError';
      this.element = element;
    }
  }

  class FieldLevelCommentWidget {
    constructor({ fieldNode, commentAdditionNode }) {
      this.fieldNode = fieldNode;
      this.contentpath = getContentPath(fieldNode);
      if (!commentAdditionNode) {
        throw new MissingElementError(commentAdditionNode);
      }
      this.commentAdditionNode = commentAdditionNode;
    }

    register() {
      if (!this.contentpath) {
        // The widget has no valid contentpath,
        // remove the button and skip subscriptions
        this.commentAdditionNode.remove();
        return undefined;
      }
      const initialState = commentApp.store.getState();
      const selectCommentsForContentPath =
        commentApp.utils.selectCommentsForContentPathFactory(this.contentpath);
      let currentComments = selectCommentsForContentPath(initialState);
      const unsubscribeWidget = commentApp.store.subscribe(() => {
        const state = commentApp.store.getState();
        const newComments = selectCommentsForContentPath(state);
        const commentsChanged = currentComments !== newComments;
        if (commentsChanged) {
          // Add annotations for any new comments
          currentComments = newComments;
          currentComments
            .filter((comment) => comment.annotation === null)
            .forEach((comment) => {
              const annotation = this.getAnnotationForComment(comment);
              commentApp.updateAnnotation(annotation, comment.localId);
              annotation.subscribeToUpdates(comment.localId);
            });
        }
      });
      initialState.comments.comments.forEach((comment) => {
        // Add annotations for any comments already in the store
        if (comment.contentpath === this.contentpath) {
          const annotation = this.getAnnotationForComment(comment);
          commentApp.updateAnnotation(annotation, comment.localId);
          annotation.subscribeToUpdates(comment.localId);
        }
      });
      const addComment = () => {
        const annotation = this.getAnnotationForComment();
        const localId = commentApp.makeComment(annotation, this.contentpath);
        annotation.subscribeToUpdates(localId);
      };
      this.commentAdditionNode.addEventListener('click', () => {
        // Open the comments side panel
        commentApp.activate();

        // Make the widget button clickable to add a comment
        addComment();
      });
      this.fieldNode.addEventListener('keyup', (e) => {
        if (isCommentShortcut(e)) {
          if (currentComments.length === 0) {
            addComment();
          } else {
            commentApp.store.dispatch(
              commentApp.actions.setFocusedComment(currentComments[0].localId, {
                updatePinnedComment: true,
                forceFocus: true,
              }),
            );
          }
        }
      });

      return unsubscribeWidget; // TODO: listen for widget deletion and use this
    }

    getAnnotationForComment() {
      const annotationNode = document
        .querySelector('#comment-icon')
        .cloneNode(true);
      annotationNode.id = '';
      annotationNode.setAttribute(
        'aria-label',
        this.commentAdditionNode.getAttribute('aria-label'),
      );
      annotationNode.setAttribute(
        'aria-describedby',
        this.commentAdditionNode.getAttribute('aria-describedby'),
      );
      annotationNode.classList.remove('!w-hidden');
      this.commentAdditionNode.insertAdjacentElement(
        'beforebegin',
        annotationNode,
      );
      return new BasicFieldLevelAnnotation(
        this.fieldNode,
        annotationNode,
        commentApp,
      );
    }
  }

  function initAddCommentButton(buttonElement) {
    const widget = new FieldLevelCommentWidget({
      fieldNode: buttonElement.closest('[data-contentpath]'),
      commentAdditionNode: buttonElement,
    });
    widget.register();
  }

  function initCommentsInterface(formElement) {
    const commentsElement = document.getElementById('comments');
    const commentsOutputElement = document.getElementById('comments-output');
    const dataElement = document.getElementById('comments-data');
    if (!commentsElement || !commentsOutputElement || !dataElement) {
      throw new Error(
        'Comments app failed to initialise. Missing HTML element',
      );
    }
    const data = JSON.parse(dataElement.textContent);
    commentApp.renderApp(
      commentsElement,
      commentsOutputElement,
      data.user,
      data.comments,
      new Map(Object.entries(data.authors)),
    );

    formElement
      .querySelectorAll('[data-component="add-comment-button"]')
      .forEach(initAddCommentButton);

    // Attach the commenting app to the tab navigation, if it exists
    const tabNavElement = formElement.querySelector(
      '[data-tabs] [role="tablist"]',
    );
    if (tabNavElement) {
      commentApp.setCurrentTab(
        tabNavElement
          .querySelector('[role="tab"][aria-selected="true"]')
          .getAttribute('href')
          .replace('#', ''),
      );
      tabNavElement.addEventListener('switch', (e) => {
        commentApp.setCurrentTab(e.detail.tab);
      });
    }

    // Show comments app
    const commentNotifications = document.querySelector(
      '[data-comment-notifications]',
    );
    commentNotifications.hidden = false;
    // Attach the comment notifications input to the form using the form attribute
    // because the input element is outside the form.
    const notificationsInput = commentNotifications.querySelector('input');
    notificationsInput.setAttribute('form', formElement.id);

    const tabContentElement = formElement.querySelector('.tab-content');
    tabContentElement.classList.add('tab-content--comments-enabled');

    // Open the comments panel whenever the comment app is activated by a user clicking on an "Add comment" widget on the form.
    const commentSidePanel = document.querySelector(
      '[data-side-panel="comments"]',
    );
    commentApp.onActivate(() => {
      commentSidePanel.dispatchEvent(new Event('open'));
    });

    // Keep number of comments up to date with comment app
    const commentCounter = document.querySelector(
      '[data-side-panel-toggle="comments"] [data-side-panel-toggle-counter]',
    );

    const updateCommentCount = () => {
      const commentCount = commentApp.selectors.selectCommentCount(
        commentApp.store.getState(),
      );

      // If comment counter element doesn't exist don't try to update innerText
      if (!commentCounter) {
        return;
      }

      if (commentCount > 0) {
        commentCounter.innerText = commentCount.toString();
        commentCounter.hidden = false;
      } else {
        // Note: Hide the circle when its content is empty
        commentCounter.hidden = true;
      }
    };
    commentApp.store.subscribe(updateCommentCount);
    updateCommentCount();
  }

  /** Add support for initializing comments via event dispatching. */
  document.addEventListener(
    'w-comments:init',
    ({ target }) => {
      setTimeout(() => {
        initCommentsInterface(target);
      });
    },
    { once: true },
  );

  return {
    commentApp,
    getContentPath,
    isCommentShortcut,
    initAddCommentButton,
    initCommentsInterface,
  };
})();
