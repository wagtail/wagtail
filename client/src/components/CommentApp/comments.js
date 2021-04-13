import { initCommentApp } from './main';
import { STRINGS } from '../../config/wagtailConfig';

const onInitCommentAppListeners = [];

function initComments(formElem) {
  window.commentApp = initCommentApp();

  // Attach the tab navigation, if the form has it
  const tabNavElem = formElem.querySelector('.tab-nav');
  if (tabNavElem) {
    window.commentApp.setCurrentTab(tabNavElem.dataset.currentTab);
    tabNavElem.addEventListener('switch', (e) => {
      window.commentApp.setCurrentTab(e.detail.tab);
    });
  }

  // Render the comments overlay
  const commentsElement = document.getElementById('comments');
  const commentsOutputElement = document.getElementById('comments-output');
  const dataElement = document.getElementById('comments-data');
  if (!commentsElement || !commentsOutputElement || !dataElement) {
    throw new Error('Comments app failed to initialise. Missing HTML element');
  }
  const data = JSON.parse(dataElement.textContent);
  window.commentApp.renderApp(
    commentsElement, commentsOutputElement, data.user, data.comments, new Map(Object.entries(data.authors)), STRINGS
  );

  // Initialise annotations
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  formElem.querySelectorAll('[data-comment-add]').forEach(initAddCommentButton);

  // Initialise comments toggle
  const commentsToggleElem = formElem.querySelector('.comments-toggle input[type=checkbox]');
  const commentNotificationsToggleElem = formElem.querySelector('.comment-notifications-toggle');
  const tabContentElem = formElem.querySelector('.tab-content');
  commentsToggleElem.addEventListener('change', (e) => {
    // Show/hide comments
    window.commentApp.setVisible(e.target.checked);

    // Show/hide comment notifications toggle
    // Add/Remove tab-nav--comments-enabled class. This changes the size of streamfields
    if (e.target.checked) {
      $(commentNotificationsToggleElem).show();
      tabContentElem.classList.add('tab-content--comments-enabled');
    } else {
      $(commentNotificationsToggleElem).hide();
      tabContentElem.classList.remove('tab-content--comments-enabled');
    }
  });

  // Keep number of comments up to date with comment app
  const commentCountElem = formElem.querySelector('.comments-toggle__count');
  const updateCommentCount = () => {
    const commentCount = window.commentApp.selectors.selectCommentCount(window.commentApp.store.getState());

    if (commentCount > 0) {
      commentCountElem.innerText = commentCount.toString();
    } else {
      // Note: CSS will hide the circle when its content is empty
      commentCountElem.innerText = '';
    }
  };
  window.commentApp.store.subscribe(updateCommentCount);
  updateCommentCount();

  // Run init event listeners
  onInitCommentAppListeners.forEach(listener => listener(window.commentApp));

  return window.commentApp;
}

function addOnInitCommentAppListener(listener) {
  onInitCommentAppListeners.push(listener);

  // Call the listener immediately if the comment app is already initialised
  if (window.commentApp) {
    listener(window.commentApp);
  }
}

export function getContentPath(fieldNode) {
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
  * @param commentApp - the commentApp the annotation is integrating with
  */
  constructor(fieldNode, node, commentApp) {
    this.node = node;
    this.fieldNode = fieldNode;
    this.unsubscribe = null;
    this.commentApp = commentApp;
  }
  /**
  * Subscribes the annotation to update when the state of a particular comment changes,
  * and to focus that comment when clicked
  * @param {number} localId - the localId of the comment to subscribe to
  */
  subscribeToUpdates(localId) {
    const { selectFocused, selectEnabled } = this.commentApp.selectors;
    const selectComment = this.commentApp.utils.selectCommentFactory(localId);
    const store = this.commentApp.store;
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
      this.commentApp.store.dispatch(
        this.commentApp.actions.setFocusedComment(localId, { updatePinnedComment: true })
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
    commentApp
  }) {
    this.fieldNode = fieldNode;
    this.contentpath = getContentPath(fieldNode);
    this.commentAdditionNode = commentAdditionNode;
    this.annotationTemplateNode = annotationTemplateNode;
    this.shown = false;
    this.commentApp = commentApp;
  }
  register() {
    const { selectEnabled } = this.commentApp.selectors;
    const initialState = this.commentApp.store.getState();
    let currentlyEnabled = selectEnabled(initialState);
    const selectCommentsForContentPath = this.commentApp.utils.selectCommentsForContentPathFactory(
      this.contentpath
    );
    let currentComments = selectCommentsForContentPath(initialState);
    this.updateVisibility(currentComments.length === 0 && currentlyEnabled);
    const unsubscribeWidget = this.commentApp.store.subscribe(() => {
      const state = this.commentApp.store.getState();
      const newComments = selectCommentsForContentPath(state);
      const newEnabled = selectEnabled(state);
      const commentsChanged = (currentComments !== newComments);
      const enabledChanged = (currentlyEnabled !== newEnabled);
      if (commentsChanged) {
        // Add annotations for any new comments
        currentComments = newComments;
        currentComments.filter((comment) => comment.annotation === null).forEach((comment) => {
          const annotation = this.getAnnotationForComment(comment);
          this.commentApp.updateAnnotation(
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
        this.commentApp.updateAnnotation(annotation, comment.localId);
        annotation.subscribeToUpdates(comment.localId);
      }
    });
    this.commentAdditionNode.addEventListener('click', () => {
      // Make the widget button clickable to add a comment
      const annotation = this.getAnnotationForComment();
      const localId = this.commentApp.makeComment(annotation, this.contentpath);
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
    return new BasicFieldLevelAnnotation(this.fieldNode, annotationNode, this.commentApp);
  }
}

const initialisedAddCommentButtons = new Set();

export function initAddCommentButton(buttonElement, skipDoubleInitialisedCheck = false) {
  // Prevent double-initialisation of the same add button
  if (!skipDoubleInitialisedCheck) {
    if (initialisedAddCommentButtons.has(buttonElement)) {
      return;
    }
    initialisedAddCommentButtons.add(buttonElement);
  }

  // If comment system not loaded yet, create a listener to set up this button when it loads
  if (!window.commentApp) {
    addOnInitCommentAppListener(() => initAddCommentButton(buttonElement, true));
    return;
  }

  const widget = new FieldLevelCommentWidget({
    fieldNode: buttonElement,
    commentAdditionNode: buttonElement,
    annotationTemplateNode: document.querySelector('#comment-icon'),
    commentApp: window.commentApp
  });
  if (widget.contentpath) {
    widget.register();
  }
}

function invalidateContentPath(contentPath) {
  if (window.commentApp) {
    window.commentApp.invalidateContentPath(contentPath);
  }
}

export default {
  getContentPath,
  initComments,
  addOnInitCommentAppListener,
  initAddCommentButton,
  invalidateContentPath,
};
