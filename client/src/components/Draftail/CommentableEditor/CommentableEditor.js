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

function CommentableEditor({commentApp, fieldNode, contentPath, rawContentState, onSave, ...options}) {
    const [editorState, setEditorState] = useState(() => createEditorStateFromRaw(rawContentState));
    const CommentControl = useMemo(() => getCommentControl(commentApp, contentPath, fieldNode), [commentApp, contentPath, fieldNode]);
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
    {...options}
  />

}

export default CommentableEditor;