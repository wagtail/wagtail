import { DraftailEditor, createEditorStateFromRaw, serialiseEditorStateToRaw } from 'draftail';
import { useEffect, useRef, useState } from 'react';


function CommentableEditor({rawContentState, onSave, ...options}) {
    const [editorState, setEditorState] = useState(() => createEditorStateFromRaw(rawContentState));

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
    {...options}
  />

}

export default CommentableEditor;