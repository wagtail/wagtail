import { initCommentApp } from '../../components/CommentApp/main';
import { STRINGS } from '../../config/wagtailConfig';

/**
 * Entry point loaded when the comments system is in use.
 */
window.comments = (() => {
  const commentApp = initCommentApp();

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
   * `getDesiredPosition` is called by the comments app to determine the height
   * at which to float the comment.
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
        const nowFocused = (selectFocused(state) === localId);
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
      }
      );
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
      this.node.ariaLabel = STRINGS.UNFOCUS_COMMENT;
    }
    onUnfocus() {
      this.node.classList.add('button-secondary');
      this.node.ariaLabel = STRINGS.FOCUS_COMMENT;
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
          commentApp.actions.setFocusedComment(localId, { updatePinnedComment: true })
        );
      });
    }
    getTab() {
      return this.fieldNode.closest('section[data-tab]')?.getAttribute('data-tab');
    }
    getDesiredPosition() {
      return (
        this.fieldNode.getBoundingClientRect().top +
        document.documentElement.scrollTop
      );
    }
  }

  class FieldLevelCommentWidget {
    constructor({
      fieldNode,
      commentAdditionNode,
      annotationTemplateNode,
    }) {
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
      const selectCommentsForContentPath = commentApp.utils.selectCommentsForContentPathFactory(
        this.contentpath
      );
      let currentComments = selectCommentsForContentPath(initialState);
      this.updateVisibility(currentComments.length === 0 && currentlyEnabled);
      const unsubscribeWidget = commentApp.store.subscribe(() => {
        const state = commentApp.store.getState();
        const newComments = selectCommentsForContentPath(state);
        const newEnabled = selectEnabled(state);
        const commentsChanged = (currentComments !== newComments);
        const enabledChanged = (currentlyEnabled !== newEnabled);
        if (commentsChanged) {
          // Add annotations for any new comments
          currentComments = newComments;
          currentComments.filter((comment) => comment.annotation === null).forEach((comment) => {
            const annotation = this.getAnnotationForComment(comment);
            commentApp.updateAnnotation(
              annotation,
              comment.localId
            );
            annotation.subscribeToUpdates(comment.localId);
          });
        }
        if (enabledChanged || commentsChanged) {
          // If comments have been enabled or disabled, or the comments have changed
          // check whether to show the widget (if comments are enabled and there are no existing comments)
          currentlyEnabled = newEnabled;
          this.updateVisibility(currentComments.length === 0 && currentlyEnabled);
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
      this.commentAdditionNode.addEventListener('click', () => {
        // Make the widget button clickable to add a comment
        const annotation = this.getAnnotationForComment();
        const localId = commentApp.makeComment(annotation, this.contentpath);
        annotation.subscribeToUpdates(localId);
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
      this.commentAdditionNode.insertAdjacentElement('afterend', annotationNode);
      return new BasicFieldLevelAnnotation(this.fieldNode, annotationNode, commentApp);
    }
  }

  function initAddCommentButton(buttonElement, skipDoubleInitialisedCheck = false) {
    const widget = new FieldLevelCommentWidget({
      fieldNode: buttonElement,
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
      throw new Error('Comments app failed to initialise. Missing HTML element');
    }
    const data = JSON.parse(dataElement.textContent);
    commentApp.renderApp(
      commentsElement, commentsOutputElement, data.user, data.comments, new Map(Object.entries(data.authors)), STRINGS
    );

    formElement.querySelectorAll('[data-component="add-comment-button"]').forEach(initAddCommentButton);

    // Attach the commenting app to the tab navigation, if it exists
    const tabNavElement = formElement.querySelector('.tab-nav');
    if (tabNavElement) {
      commentApp.setCurrentTab(tabNavElement.dataset.currentTab);
      tabNavElement.addEventListener('switch', (e) => {
        commentApp.setCurrentTab(e.detail.tab);
      });
    }

    // Comments toggle
    const commentToggle = formElement.querySelector('.comments-toggle input[type=checkbox]');
    const commentNotificationsToggle = formElement.querySelector('.comment-notifications-toggle');
    const tabContentElement = formElement.querySelector('.tab-content');
    commentToggle.addEventListener('change', (e) => {
      // Show/hide comments
      commentApp.setVisible(e.target.checked);

      // Show/hide comment notifications toggle
      // Add/Remove tab-nav--comments-enabled class. This changes the size of streamfields
      if (e.target.checked) {
        $(commentNotificationsToggle).show();
        tabContentElement.classList.add('tab-content--comments-enabled');
      } else {
        $(commentNotificationsToggle).hide();
        tabContentElement.classList.remove('tab-content--comments-enabled');
      }
    });

    // Keep number of comments up to date with comment app
    const commentCounter = formElement.querySelector('.comments-toggle__count');
    const updateCommentCount = () => {
      const commentCount = commentApp.selectors.selectCommentCount(commentApp.store.getState());

      if (commentCount > 0) {
        commentCounter.innerText = commentCount.toString();
      } else {
        // Note: CSS will hide the circle when its content is empty
        commentCounter.innerText = '';
      }
    };
    commentApp.store.subscribe(updateCommentCount);
    updateCommentCount();
  }

  return {
    commentApp,
    getContentPath,
    initAddCommentButton,
    initCommentsInterface,
  };
})();
