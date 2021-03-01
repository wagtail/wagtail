import { DraftailEditor, ToolbarButton, createEditorStateFromRaw, serialiseEditorStateToRaw } from 'draftail';
import { RichUtils } from 'draft-js';
import { useEffect, useMemo, useRef, useState } from 'react';

import { STRINGS } from '../../../config/wagtailConfig';
import Icon from '../../Icon/Icon';
import { useSelector } from 'react-redux';

class DraftailInlineAnnotation {
    constructor(field) {
      this.field = field;
      this.inlineRefs = new Set()
    }
    addRef(ref) {
      this.inlineRefs.add(ref);
    }
    removeRef(ref) {
      this.inlineRefs.delete(ref);
    }
    getDesiredPosition() {
      const nodeTops = Array.from(this.inlineRefs).map(ref => ref.current).filter(node => node).map(node => node.getBoundingClientRect().top)
      if (nodeTops.length > 0) {
        return nodeTops.reduce((a,b) => a + b, 0)/nodeTops.length + document.documentElement.scrollTop
      }
      const fieldNode = this.field
      if (fieldNode) {
        return fieldNode.getBoundingClientRect().top + document.documentElement.scrollTop
      }
      return 0
    }
}

function getCommentControl(commentApp, contentPath, fieldNode) {
  return ({getEditorState, onChange}) => {
    return <ToolbarButton
      name='comment'
      active={false}
      title={STRINGS.ADD_A_COMMENT}
      icon={<Icon name="comment"/>}
      onClick={() => {
        const annotation = new DraftailInlineAnnotation(fieldNode)
        const commentId = commentApp.makeComment(annotation, contentPath);
        onChange(RichUtils.toggleInlineStyle(getEditorState(), `COMMENT-${commentId}`))
      }}
    />
  }
}

function findCommentStyleRanges(contentBlock, callback) {
    contentBlock.findStyleRanges((metadata) => metadata.getStyle().some((style) => style.startsWith('COMMENT')), (start, end) => {callback(start, end)})
}

function getCommentDecorator(commentApp) {
  const CommentDecorator = ({ contentState, children }) => {
    // The comment decorator makes a comment clickable, allowing it to be focused.
    // It does not provide styling, as draft-js imposes a 1 decorator/string limit, which would prevent comment highlights
    // going over links/other entities
    const blockKey = children[0].props.block.getKey()
    const start = children[0].props.start
    const commentId = useMemo(() => parseInt(contentState.getBlockForKey(blockKey).getInlineStyleAt(start).find((style) => style.startsWith('COMMENT')).slice(8)), [blockKey, start]);
    const annotationNode = useRef(null);
    useEffect(() => {
      // Add a ref to the annotation, allowing the comment to float alongside the attached text.
      // This adds rather than sets the ref, so that a comment may be attached across paragraphs or around entities
      const annotation = commentApp.layout.commentAnnotations.get(commentId)
      if (annotation) {
        annotation.addRef(annotationNode);
      }
      return () => {
        const annotation = commentApp.layout.commentAnnotations.get(commentId)
        if (annotation) {
          annotation.removeRef(annotationNode);
        }
      }
    });
    const onClick = () => {
      // Pin and focus the clicked comment
      commentApp.store.dispatch(
        commentApp.actions.setFocusedComment(commentId)
      );
      commentApp.store.dispatch(
        commentApp.actions.setPinnedComment(commentId)
      );
    }
    // TODO: determine the correct way to make this accessible, allowing both editing and focus jumps
    return (
      <a 
        type="button"
        ref={annotationNode}
        onClick={onClick}
        data-annotation
      >
        {children}
      </a>
    )
  }
  return CommentDecorator
}

function CommentableEditor({commentApp, fieldNode, contentPath, rawContentState, onSave, ...options}) {
    const [editorState, setEditorState] = useState(() => createEditorStateFromRaw(rawContentState));
    const CommentControl = useMemo(() => getCommentControl(commentApp, contentPath, fieldNode), [commentApp, contentPath, fieldNode]);
    const CommentDecorator = useMemo(() => getCommentDecorator(commentApp), [commentApp])
    const enabled = useSelector(commentApp.selectors.selectEnabled);

    const timeoutRef = useRef();
    useEffect(() => {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = window.setTimeout(
        onSave(serialiseEditorStateToRaw(editorState)),
        250,
      );
      return () => {
        onSave(serialiseEditorStateToRaw(editorState));
        window.clearTimeout(timeoutRef.current);
      }
    }, [editorState]);

    return <DraftailEditor
    onChange={setEditorState}
    editorState={editorState}
    controls={enabled ? [CommentControl] : []}
    decorators={enabled ? [{
      strategy: findCommentStyleRanges,
      component: CommentDecorator 
    }] : []}
    {...options}
  />

}

export default CommentableEditor;