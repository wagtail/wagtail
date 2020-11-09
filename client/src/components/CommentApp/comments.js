import { initCommentsApp } from 'wagtail-comment-frontend';
import { STRINGS } from '../../config/wagtailConfig';

function initComments(element, author, initialComments) {
    const app = initCommentsApp(element, author, initialComments, STRINGS);
    window.commentApp = app;
    return app
}

function initFieldLevelCommentWidget(fieldElement) {
    let widget = new comments.FieldLevelCommentWidget(fieldElement, fieldElement.querySelector('[data-comment-add]'), document.querySelector('#comment-icon'), window.commentApp)
    widget.register();
}

function prepareFieldLevelCommentInit(fieldSelector) {
    if (window.commentApp) {
        initFieldLevelCommentWidget(fieldSelector);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            initFieldLevelCommentWidget(fieldSelector);
        });
        
    }
}

function getContentPath(fieldNode) {
    // Return the total contentpath for an element as a string, in the form field.streamfield_uid.block...
    if (fieldNode.closest('data-contentpath-disabled')) {
        return ''
    }
    let element = fieldNode.closest('[data-contentpath]');
    let contentPaths = [];
    while (element!== null) {
        contentPaths.push(element.dataset.contentpath);
        element = element.parentElement.closest('[data-contentpath]');
    }
    contentPaths.reverse();
    return contentPaths.join('.')
}

class BasicFieldLevelAnnotation {
    constructor(fieldNode, node) {
        this.node = node;
        this.fieldNode = fieldNode;
    }
    position = ''
    onDelete() {
        this.node.remove();
    }
    onFocus() {
        this.node.classList.remove("button-secondary")
        this.node.ariaLabel = STRINGS.UNFOCUS_COMMENT;
    }
    onUnfocus() {
        this.node.classList.add("button-secondary")
        this.node.ariaLabel = STRINGS.UNFOCUS_COMMENT;
        // TODO: ensure comment is focused accessibly when this is clicked, 
        // and that screenreader users can return to the annotation point when desired
    }
    show() {
        this.node.classList.remove('u-hidden');
    }
    hide() {
        this.node.classList.add('u-hidden');
    }
    setOnClickHandler(handler) {
        this.node.addEventListener('click', handler);
    }
    getDesiredPosition() {
        return this.fieldNode.getBoundingClientRect().top + document.documentElement.scrollTop
    }
}

class FieldLevelCommentWidget {
    constructor(fieldNode, commentAdditionNode, annotationTemplateNode, commentApp) {
      let self = this;
      this.fieldNode = fieldNode;
      this.contentPath = getContentPath(fieldNode);
      this.commentAdditionNode = commentAdditionNode;
      this.commentApp = commentApp;
      this.annotationTemplateNode = annotationTemplateNode;
      commentAdditionNode.addEventListener('click', self.addComment.bind(self));
      this.commentNumber = 0;
      this.commentsEnabled = false;
    }
    register() {
        // if the widget has a contentpath - ie commenting is enabled for this field -
        // register the widget with the comment app to subscribe to updates on comments for 
        // this widget's contentpath, and to commenting enabled/disabled updates
        if (this.contentPath) {
            this.commentApp.registerWidget(this);
        }
    }
    setEnabled(enabled) {
        // Update whether comments are enabled for the page
        this.commentsEnabled = enabled;
        this.updateVisibility();
    }
    onChangeComments(comments) {
        // Receives a list of comments for the widget's contentpath
        this.commentNumber = comments.length;
        this.updateVisibility();
    }
    updateVisibility() {
        // if comments are disabled, or the widget already has at least one associated comment, don't show the comment addition button
        (!this.commentsEnabled) || this.commentNumber > 0 ? this.commentAdditionNode.classList.add('u-hidden') : this.commentAdditionNode.classList.remove('u-hidden');
    }
    getAnnotationForComment() {
        let annotationNode = this.annotationTemplateNode.cloneNode(true);
        annotationNode.id = '';
        this.commentAdditionNode.insertAdjacentElement('afterend', annotationNode);
        return new BasicFieldLevelAnnotation(this.fieldNode, annotationNode)
    }
    addComment() {
        this.commentApp.makeComment(this.getAnnotationForComment(), this.contentPath);
    }
  }

export default {
    initComments, FieldLevelCommentWidget, initFieldLevelCommentWidget, prepareFieldLevelCommentInit
}