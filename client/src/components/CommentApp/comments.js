import { initCommentsApp } from 'wagtail-comment-frontend';
import { STRINGS } from '../../config/wagtailConfig';

function initComments(element, author, initialComments, addAnnotatableSections) {
    return initCommentsApp(element, author, initialComments, addAnnotatableSections, STRINGS);
}

let testnumber = 1
function getContentPath(fieldNode) {
    testnumber += 1;
    return 'test' + testnumber 
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
    setEnabled(enabled) {
        this.commentsEnabled = enabled;
        this.updateVisibility();
    }
    onChangeComments(comments) {
        this.commentNumber = comments.length;
        this.updateVisibility();
    }
    updateVisibility() {
        (!this.commentsEnabled) || this.commentNumber > 0 ? this.commentAdditionNode.classList.add('u-hidden') : this.commentAdditionNode.classList.remove('u-hidden');
    }
    getAnnotationForComment() {
        let annotationNode = this.annotationTemplateNode.cloneNode(true);
        annotationNode.id = '';
        this.commentAdditionNode.insertAdjacentElement('afterend', annotationNode);
        this.commentNumber += 1;
        this.updateVisibility();
        return new BasicFieldLevelAnnotation(this.fieldNode, annotationNode)
    }
    addComment() {
        this.commentApp.makeComment(this.getAnnotationForComment(), this.contentPath);
    }
  }

export default {
    initComments, FieldLevelCommentWidget
}