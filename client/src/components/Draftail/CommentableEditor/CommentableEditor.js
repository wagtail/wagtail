import { DraftailEditor, ToolbarButton, createEditorStateFromRaw, serialiseEditorStateToRaw } from 'draftail';
import { EditorState, Modifier, RichUtils, SelectionState } from 'draft-js';
import { filterInlineStyles } from "draftjs-filters";
import { useEffect, useMemo, useRef, useState } from 'react';
import { useSelector, shallowEqual } from 'react-redux';

import { STRINGS } from '../../../config/wagtailConfig';
import Icon from '../../Icon/Icon';

const COMMENT_STYLE_IDENTIFIER = 'COMMENT-'

function usePrevious(value) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

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

/**
 * Get a selection state corresponding to the full contentState.
 */
function getFullSelectionState(contentState) {
  const lastBlock = contentState.getLastBlock();
  let fullSelectionState = SelectionState.createEmpty();
  fullSelectionState = fullSelectionState.set('anchorKey', contentState.getFirstBlock().getKey());
  fullSelectionState = fullSelectionState.set('focusKey', lastBlock.getKey());
  fullSelectionState = fullSelectionState.set('anchorOffset', 0);
  fullSelectionState = fullSelectionState.set('focusOffset', lastBlock.getLength());
  return fullSelectionState
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
        onChange(RichUtils.toggleInlineStyle(getEditorState(), `${COMMENT_STYLE_IDENTIFIER}${commentId}`))
      }}
    />
  }
}

function findCommentStyleRanges(contentBlock, callback) {
    contentBlock.findStyleRanges((metadata) => metadata.getStyle().some((style) => style.startsWith(COMMENT_STYLE_IDENTIFIER)), (start, end) => {callback(start, end)})
}

function getCommentDecorator(commentApp) {
  const CommentDecorator = ({ contentState, children }) => {
    // The comment decorator makes a comment clickable, allowing it to be focused.
    // It does not provide styling, as draft-js imposes a 1 decorator/string limit, which would prevent comment highlights
    // going over links/other entities
    const blockKey = children[0].props.block.getKey()
    const start = children[0].props.start

    const commentId = useMemo(() => parseInt(contentState.getBlockForKey(blockKey).getInlineStyleAt(start).find((style) => style.startsWith(COMMENT_STYLE_IDENTIFIER)).slice(8)), [blockKey, start]);
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
      <span 
        role="button"
        ref={annotationNode}
        onClick={onClick}
        data-annotation
      >
        {children}
      </span>
    )
  }
  return CommentDecorator
}

function forceResetEditorState(editorState, replacementContent) {
  const content = replacementContent ? replacementContent : editorState.getCurrentContent()
  const state = EditorState.set(
    EditorState.createWithContent(
      content,
      editorState.getDecorator(),
    ),
    {
      selection: editorState.getSelection(),
      undoStack: editorState.getUndoStack(),
      redoStack: editorState.getRedoStack(),
    },
  );
  return EditorState.acceptSelection(state, state.getSelection())
};

function CommentableEditor({commentApp, fieldNode, contentPath, rawContentState, onSave, inlineStyles, editorRef, ...options}) {
    const [editorState, setEditorState] = useState(() => createEditorStateFromRaw(rawContentState));
    const CommentControl = useMemo(() => getCommentControl(commentApp, contentPath, fieldNode), [commentApp, contentPath, fieldNode]);
    const commentsSelector = useMemo(() => commentApp.utils.selectCommentsForContentPathFactory(contentPath), [contentPath, commentApp]);
    const CommentDecorator = useMemo(() => getCommentDecorator(commentApp), [commentApp])
    const comments = useSelector(commentsSelector, shallowEqual);
    const enabled = useSelector(commentApp.selectors.selectEnabled);
    const focusedId = useSelector(commentApp.selectors.selectFocused);

    const ids = useMemo(() => comments.map(comment => comment.localId), [comments]);

    const commentStyles = useMemo(() => ids.map(id => {return {
      type: `${COMMENT_STYLE_IDENTIFIER}${id}`,
      style: enabled ? {
        'background-color': (focusedId !== id) ? '#01afb0' : '#007d7e'
      } : {}
    }}), [ids, enabled]);

    const [uniqueStyleId, setUniqueStyleId] = useState(0)

    const previousFocused = usePrevious(focusedId);
    const previousIds = usePrevious(ids);
    const previousEnabled = usePrevious(enabled);
    useEffect(() => {
      // Only trigger a focus-related rerender if the current focused comment is inside the field, or the previous one was
      const validFocusChange = previousFocused !== focusedId && (previousIds && previousIds.includes(previousFocused) || ids.includes(focusedId))

      if ((!validFocusChange) && previousIds === ids && previousEnabled === enabled) {
        return
      }

      // Filter out any invalid styles - deleted comments, or now unneeded STYLE_RERENDER forcing styles
      const filteredContent = filterInlineStyles(inlineStyles.map(style => style.type).concat(ids.map(id => `${COMMENT_STYLE_IDENTIFIER}${id}`)), editorState.getCurrentContent())
      // Force reset the editor state to ensure redecoration, and apply a new (blank) inline style to force inline style rerender
      // This must be entirely new for the rerender to trigger, hence the unique style id, as with the undo stack we cannot guarantee
      // that a previous style won't persist without filtering everywhere, which seems a bit too heavyweight
      // This hack can be removed when draft-js triggers inline style rerender on props change
      setEditorState(editorState => forceResetEditorState(editorState, 
        Modifier.applyInlineStyle(
          filteredContent,
          getFullSelectionState(filteredContent),
          `STYLE_RERENDER_'${uniqueStyleId}`
        )
      ))
      setUniqueStyleId((id) => (id + 1) % 200);
    }, [focusedId, enabled, inlineStyles, ids, editorState])

    const timeoutRef = useRef();
    useEffect(() => {
      // This replicates the onSave logic in Draftail, but only saves the state with all
      // comment styles filtered out
      window.clearTimeout(timeoutRef.current);
      const filteredEditorState = EditorState.push(
        editorState,
        filterInlineStyles(inlineStyles.map(style => style.type), editorState.getCurrentContent())
      );
      timeoutRef.current = window.setTimeout(
        onSave(serialiseEditorStateToRaw(filteredEditorState)),
        250,
      );
      return () => {
        window.clearTimeout(timeoutRef.current);
      }
    }, [editorState, inlineStyles]);

    return <DraftailEditor
    ref={editorRef}
    onChange={setEditorState}
    editorState={editorState}
    controls={enabled ? [CommentControl] : []}
    decorators={enabled ? [{
      strategy: findCommentStyleRanges,
      component: CommentDecorator 
    }] : []}
    inlineStyles={inlineStyles.concat(commentStyles)}
    {...options}
  />

}

export default CommentableEditor;
