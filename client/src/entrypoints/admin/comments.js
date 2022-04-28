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
    if (fieldNode.closest('data-contentpath-disabled')) {
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
      const { selectFocused, selectEnabled } = commentApp.selectors;
      const selectComment = commentApp.utils.selectCommentFactory(localId);
      const store = commentApp.store;
      const initialState = store.getState();
      let focused = selectFocused(initialState) === localId;
      let shown = selectEnabled(initialState);
      if (focused) {
        this.onFocus();
      }
      if (shown) {
        this.show();
      }
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
        if (shown !== selectEnabled(state)) {
          if (shown) {
            this.hide();
          } else {
            this.show();
          }
          shown = selectEnabled(state);
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
      this.node.classList.remove('button-secondary');
      this.node.ariaLabel = gettext('Unfocus comment');
    }

    onUnfocus() {
      this.node.classList.add('button-secondary');
      this.node.ariaLabel = gettext('Focus comment');

      // TODO: ensure comment is focused accessibly when this is clicked,
      // and that screenreader users can return to the annotation point when desired
    }

    show() {
      this.node.classList.remove('u-hidden');
    }

    hide() {
      this.node.classList.add('u-hidden');
    }

    setOnClickHandler(localId) {
      this.node.addEventListener('click', () => {
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

  class FieldLevelCommentWidget {
    constructor({ fieldNode, commentAdditionNode, annotationTemplateNode }) {
      this.fieldNode = fieldNode;
      this.contentpath = getContentPath(fieldNode);
      this.commentAdditionNode = commentAdditionNode;
      this.annotationTemplateNode = annotationTemplateNode;
      this.shown = false;
    }

    register() {
      const { selectEnabled } = commentApp.selectors;
      const initialState = commentApp.store.getState();
      let currentlyEnabled = selectEnabled(initialState);
      const selectCommentsForContentPath =
        commentApp.utils.selectCommentsForContentPathFactory(this.contentpath);
      let currentComments = selectCommentsForContentPath(initialState);
      this.updateVisibility(currentComments.length === 0 && currentlyEnabled);
      const unsubscribeWidget = commentApp.store.subscribe(() => {
        const state = commentApp.store.getState();
        const newComments = selectCommentsForContentPath(state);
        const newEnabled = selectEnabled(state);
        const commentsChanged = currentComments !== newComments;
        const enabledChanged = currentlyEnabled !== newEnabled;
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
        if (enabledChanged || commentsChanged) {
          // If comments have been enabled or disabled, or the comments have changed
          // check whether to show the widget (if comments are enabled and there are no existing comments)
          currentlyEnabled = newEnabled;
          this.updateVisibility(
            currentComments.length === 0 && currentlyEnabled,
          );
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
        // Make the widget button clickable to add a comment
        addComment();
      });
      this.fieldNode.addEventListener('keyup', (e) => {
        if (currentlyEnabled && isCommentShortcut(e)) {
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

    updateVisibility(newShown) {
      if (newShown === this.shown) {
        return;
      }
      this.shown = newShown;

      if (!this.shown) {
        this.commentAdditionNode.classList.add('u-hidden');
      } else {
        this.commentAdditionNode.classList.remove('u-hidden');
      }
    }

    getAnnotationForComment() {
      const annotationNode = this.annotationTemplateNode.cloneNode(true);
      annotationNode.id = '';
      annotationNode.classList.remove('u-hidden');
      this.commentAdditionNode.insertAdjacentElement(
        'afterend',
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
      annotationTemplateNode: document.querySelector('#comment-icon'),
    });
    if (widget.contentpath) {
      widget.register();
    }
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

    // Show/hide comments when the side panel is opened/closed
    const commentsSidePanel = document.querySelector(
      '[data-side-panel="comments"]',
    );
    const commentNotifications = formElement.querySelector(
      '[data-comment-notifications]',
    );
    const tabContentElement = formElement.querySelector('.tab-content');

    const updateCommentVisibility = (visible) => {
      // Show/hide comments
      commentApp.setVisible(visible);

      // Add/Remove tab-nav--comments-enabled class. This changes the size of streamfields
      if (visible) {
        tabContentElement.classList.add('tab-content--comments-enabled');
        if (commentNotifications) {
          commentNotifications.hidden = false;
        }
      } else {
        tabContentElement.classList.remove('tab-content--comments-enabled');
        if (commentNotifications) {
          commentNotifications.hidden = true;
        }
      }
    };

    if (commentsSidePanel) {
      commentsSidePanel.addEventListener('show', () => {
        updateCommentVisibility(true);
      });

      commentsSidePanel.addEventListener('hide', () => {
        updateCommentVisibility(false);
      });
    }

    // Keep number of comments up to date with comment app
    const commentToggle = document.querySelector(
      '[data-side-panel-toggle="comments"]',
    );

    const commentCounter = document.createElement('div');
    commentCounter.className =
      '-w-mr-3 w-py-0.5 w-px-[0.325rem] w-translate-y-[-8px] w-translate-x-[-4px] w-text-[0.5625rem] w-font-bold w-bg-teal-100 w-text-white w-border w-border-white w-rounded-[1rem]';
    commentToggle.className =
      'w-h-[50px] w-bg-transparent w-box-border w-py-3 w-px-3 w-flex w-justify-center w-items-center w-outline-offset-inside w-text-grey-400 w-transition hover:w-transform hover:w-scale-110 hover:w-text-primary focus:w-text-primary';
    commentToggle.appendChild(commentCounter);

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
      } else {
        // Note: Hide the circle when its content is empty
        commentCounter.hidden = true;
      }
    };
    commentApp.store.subscribe(updateCommentCount);
    updateCommentCount();
  }

  return {
    commentApp,
    getContentPath,
    isCommentShortcut,
    initAddCommentButton,
    initCommentsInterface,
  };
})();
