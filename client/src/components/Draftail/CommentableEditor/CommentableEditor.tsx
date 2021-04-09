import type { CommentApp } from '../../CommentApp/main';
import type { Annotation } from '../../CommentApp/utils/annotation';
import type { Comment } from '../../CommentApp/state/comments';
import {
  DraftailEditor,
  ToolbarButton,
  createEditorStateFromRaw,
  serialiseEditorStateToRaw,
} from 'draftail';
import {
  CharacterMetadata,
  ContentBlock,
  ContentState,
  DraftInlineStyle,
  EditorState,
  Modifier,
  RawDraftContentState,
  RichUtils,
  SelectionState
} from 'draft-js';
import type { DraftEditorLeaf } from 'draft-js/lib/DraftEditorLeaf.react';
import { filterInlineStyles } from 'draftjs-filters';
import React, { MutableRefObject, ReactText, useEffect, useMemo, useRef, useState } from 'react';
import { useSelector, shallowEqual } from 'react-redux';

import { STRINGS } from '../../../config/wagtailConfig';
import Icon from '../../Icon/Icon';

const COMMENT_STYLE_IDENTIFIER = 'COMMENT-';

function usePrevious<Type>(value: Type) {
  const ref = useRef(value);
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

type DecoratorRef = MutableRefObject<HTMLSpanElement | null>;
type BlockKey = string;

/**
 * Controls the positioning of a comment that has been added to Draftail.
 * `getDesiredPosition` is called by the comments app to determine the height
 * at which to float the comment.
 */
class DraftailInlineAnnotation implements Annotation {
  /**
   * Create an inline annotation
   * @param {Element} field - an element to provide the fallback position for comments without any inline decorators
   */
  field: Element
  decoratorRefs: Map<DecoratorRef, BlockKey>
  focusedBlockKey: BlockKey
  cachedMedianRef: DecoratorRef | null

  constructor(field: Element) {
    this.field = field;
    this.decoratorRefs = new Map();
    this.focusedBlockKey = '';
    this.cachedMedianRef = null;
  }
  addDecoratorRef(ref: DecoratorRef, blockKey: BlockKey) {
    this.decoratorRefs.set(ref, blockKey);

    // We're adding a ref, so remove the cached median refs - this needs to be recalculated
    this.cachedMedianRef = null;
  }
  removeDecoratorRef(ref: DecoratorRef) {
    this.decoratorRefs.delete(ref);

    // We're deleting a ref, so remove the cached median refs - this needs to be recalculated
    this.cachedMedianRef = null;
  }
  setFocusedBlockKey(blockKey: BlockKey) {
    this.focusedBlockKey = blockKey;
  }
  static getHeightForRef(ref: DecoratorRef) {
    if (ref.current) {
      return ref.current.getBoundingClientRect().top;
    }
    return 0;
  }
  static getMedianRef(refArray: Array<DecoratorRef>) {
    const refs = refArray.sort(
      (firstRef, secondRef) => this.getHeightForRef(firstRef) - this.getHeightForRef(secondRef)
    );
    const length = refs.length;
    if (length > 0) {
      return refs[Math.ceil(length / 2 - 1)];
    }
    return null;
  }
  getTab() {
    return this.field.closest('section[data-tab]')?.getAttribute('data-tab');
  }
  getDesiredPosition(focused = false) {
    // The comment should always aim to float by an annotation, rather than between them
    // so calculate which annotation is the median one by height and float the comment by that
    let medianRef: null | DecoratorRef = null;
    if (focused) {
      // If the comment is focused, calculate the median of refs only
      // within the focused block, to ensure the comment is visisble
      // if the highlight has somehow been split up
      medianRef = DraftailInlineAnnotation.getMedianRef(
        Array.from(this.decoratorRefs.keys()).filter(
          (ref) => this.decoratorRefs.get(ref) === this.focusedBlockKey
        )
      );
    } else if (!this.cachedMedianRef) {
      // Our cache is empty - try to update it
      medianRef = DraftailInlineAnnotation.getMedianRef(
        Array.from(this.decoratorRefs.keys())
      );
      this.cachedMedianRef = medianRef;
    } else {
      // Use the cached median refs
      medianRef = this.cachedMedianRef;
    }

    if (medianRef) {
      // We have a median ref - calculate its height
      return (
        DraftailInlineAnnotation.getHeightForRef(medianRef) +
        document.documentElement.scrollTop
      );
    }

    const fieldNode = this.field;
    if (fieldNode) {
      // Fallback to the field node, if the comment has no decorator refs
      return (
        fieldNode.getBoundingClientRect().top +
        document.documentElement.scrollTop
      );
    }
    return 0;
  }
}


function applyInlineStyleToRange({ contentState, style, blockKey, start, end }:
  {contentState: ContentState,
    style: string,
    blockKey: BlockKey,
    start: number,
    end: number}
) {
  return Modifier.applyInlineStyle(contentState,
    new SelectionState({
      anchorKey: blockKey,
      anchorOffset: start,
      focusKey: blockKey,
      focusOffset: end
    }),
    style
  );
}

/**
 * Get a selection state corresponding to the full contentState.
 */
function getFullSelectionState(contentState: ContentState) {
  const lastBlock = contentState.getLastBlock();
  return new SelectionState({
    anchorKey: contentState.getFirstBlock().getKey(),
    anchorOffset: 0,
    focusKey: lastBlock.getKey(),
    focusOffset: lastBlock.getLength()
  });
}

interface ControlProps {
  getEditorState: () => EditorState,
  onChange: (editorState: EditorState) => void
}

function getCommentControl(commentApp: CommentApp, contentPath: string, fieldNode: Element) {
  return ({ getEditorState, onChange }: ControlProps) => (
    <span className="Draftail-CommentControl" data-comment-add>
      <ToolbarButton
        name="comment"
        active={false}
        title={STRINGS.ADD_A_COMMENT}
        icon={<Icon name="comment" />}
        onClick={() => {
          const annotation = new DraftailInlineAnnotation(fieldNode);
          const commentId = commentApp.makeComment(annotation, contentPath, '[]');
          const editorState = getEditorState();
          onChange(
            EditorState.acceptSelection(
              RichUtils.toggleInlineStyle(
                editorState,
                `${COMMENT_STYLE_IDENTIFIER}${commentId}`
              ),
              editorState.getSelection()
            )
          );
        }}
      />
    </span>
  );
}

function styleIsComment(style: string | undefined): style is string {
  return style !== undefined && style.startsWith(COMMENT_STYLE_IDENTIFIER);
}

function getIdForCommentStyle(style: string) {
  return parseInt(style.slice(COMMENT_STYLE_IDENTIFIER.length), 10);
}

function findCommentStyleRanges(
  contentBlock: ContentBlock,
  callback: (start: number, end: number) => void,
  filterFn?: (metadata: CharacterMetadata) => boolean) {
  // Find comment style ranges that do not overlap an existing entity
  const filterFunction = filterFn || ((metadata: CharacterMetadata) => metadata.getStyle().some(styleIsComment));
  const entityRanges: Array<[number, number]> = [];
  contentBlock.findEntityRanges(
    character => character.getEntity() !== null,
    (start, end) => entityRanges.push([start, end])
  );
  contentBlock.findStyleRanges(
    filterFunction,
    (start, end) => {
      const interferingEntityRanges = entityRanges.filter(value => value[1] > start).filter(value => value[0] < end);
      let currentPosition = start;
      interferingEntityRanges.forEach((value) => {
        const [entityStart, entityEnd] = value;
        if (entityStart > currentPosition) {
          callback(currentPosition, entityStart);
        }
        currentPosition = entityEnd;
      });
      if (currentPosition < end) {
        callback(start, end);
      }
    }
  );
}


function updateCommentPositions({ editorState, comments, commentApp }:
  {
    editorState: EditorState,
    comments: Array<Comment>,
    commentApp: CommentApp
  }) {
  // Construct a map of comment id -> array of style ranges
  const commentPositions = new Map();

  editorState.getCurrentContent().getBlocksAsArray().forEach(
    (block) => {
      const key = block.getKey();
      block.findStyleRanges((metadata) => metadata.getStyle().some(styleIsComment),
        (start, end) => {
          block.getInlineStyleAt(start).filter(styleIsComment).forEach(
            (style) => {
              // We have already filtered out any undefined styles, so cast here
              const id = getIdForCommentStyle(style as string);
              let existingPosition = commentPositions.get(id);
              if (!existingPosition) {
                existingPosition = [];
              }
              existingPosition.push({
                key: key,
                start: start,
                end: end
              });
              commentPositions.set(id, existingPosition);
            }
          );
        });
    }
  );


  comments.filter(comment => comment.annotation).forEach((comment) => {
    // if a comment has an annotation - ie the field has it inserted - update its position
    const newPosition = commentPositions.get(comment.localId);
    const serializedNewPosition = newPosition ? JSON.stringify(newPosition) : '[]';
    if (comment.position !== serializedNewPosition) {
      commentApp.store.dispatch(
        commentApp.actions.updateComment(
          comment.localId,
          { position: serializedNewPosition }
        )
      );
    }
  });
}

interface DecoratorProps {
  contentState: ContentState,
  children?: Array<DraftEditorLeaf>
}

function getCommentDecorator(commentApp: CommentApp) {
  const CommentDecorator = ({ contentState, children }: DecoratorProps) => {
    // The comment decorator makes a comment clickable, allowing it to be focused.
    // It does not provide styling, as draft-js imposes a 1 decorator/string limit,
    // which would prevent comment highlights going over links/other entities
    if (!children) {
      return null;
    }
    const blockKey: BlockKey = children[0].props.block.getKey();
    const start: number = children[0].props.start;

    const commentId = useMemo(
      () => {
        const block = contentState.getBlockForKey(blockKey);
        const styles = block.getInlineStyleAt(start).filter(styleIsComment) as Immutable.OrderedSet<string>;
        let styleToUse: string;
        if (styles.count() > 1) {
          // We're dealing with overlapping comments.
          // Find the least frequently occurring style and use that - this isn't foolproof, but in
          // most cases should ensure that all comments have at least one clickable section. This
          // logic is a bit heavier than ideal for a decorator given how often we are forced to
          // redecorate, but will only be used on overlapping comments

          // Use of casting in this function is due to issue #1563 in immutable-js, which causes operations like
          // map and filter to lose type information on the results. It should be fixed in v4: when we upgrade,
          // this casting should be removed
          let styleFreq = styles.map((style) => {
            let counter = 0;
            findCommentStyleRanges(block,
              () => { counter = counter + 1; },
              (metadata) => metadata.getStyle().some(rangeStyle => rangeStyle === style)
            );
            return [style, counter];
          }) as unknown as Immutable.OrderedSet<[string, number]>;

          styleFreq =  styleFreq.sort(
            (firstStyleCount, secondStyleCount) => firstStyleCount[1] - secondStyleCount[1]
          ) as Immutable.OrderedSet<[string, number]>;

          styleToUse = styleFreq.first()[0];
        } else {
          styleToUse = styles.first();
        }
        return getIdForCommentStyle(styleToUse);
      }, [blockKey, start]);
    const annotationNode = useRef(null);
    useEffect(() => {
      // Add a ref to the annotation, allowing the comment to float alongside the attached text.
      // This adds rather than sets the ref, so that a comment may be attached across paragraphs or around entities
      const annotation = commentApp.layout.commentAnnotations.get(commentId);
      if (annotation && annotation instanceof DraftailInlineAnnotation) {
        annotation.addDecoratorRef(annotationNode, blockKey);
        return () => annotation.removeDecoratorRef(annotationNode);
      }
      return undefined; // eslint demands an explicit return here
    }, [commentId, annotationNode, blockKey]);
    const onClick = () => {
      // Ensure the comment will appear alongside the current block
      const annotation = commentApp.layout.commentAnnotations.get(commentId);
      if (annotation && annotation instanceof DraftailInlineAnnotation  && annotationNode) {
        annotation.setFocusedBlockKey(blockKey);
      }

      // Pin and focus the clicked comment
      commentApp.store.dispatch(
        commentApp.actions.setFocusedComment(commentId, {
          updatePinnedComment: true,
        })
      );
    };
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
    );
  };
  return CommentDecorator;
}

function forceResetEditorState(editorState: EditorState, replacementContent: ContentState) {
  const content = replacementContent || editorState.getCurrentContent();
  const state = EditorState.set(
    EditorState.createWithContent(content, editorState.getDecorator()),
    {
      selection: editorState.getSelection(),
      undoStack: editorState.getUndoStack(),
      redoStack: editorState.getRedoStack(),
    }
  );
  return EditorState.acceptSelection(state, state.getSelection());
}

interface InlineStyle {
  label?: string,
  description?: string,
  icon?: string | string[] | Node,
  type: string,
  style?: Record<string, string | number | ReactText | undefined >
}

interface ColorConfigProp {
  standardHighlight: string,
  overlappingHighlight: string,
  focusedHighlight: string
}

interface CommentableEditorProps {
  commentApp: CommentApp,
  fieldNode: Element,
  contentPath: string,
  rawContentState: RawDraftContentState,
  onSave: (rawContent: RawDraftContentState) => void,
  inlineStyles: Array<InlineStyle>,
  editorRef: MutableRefObject<HTMLInputElement>
  colorConfig: ColorConfigProp
}

function CommentableEditor({
  commentApp,
  fieldNode,
  contentPath,
  rawContentState,
  onSave,
  inlineStyles,
  editorRef,
  colorConfig: { standardHighlight, overlappingHighlight, focusedHighlight },
  ...options
}: CommentableEditorProps) {
  const [editorState, setEditorState] = useState(() =>
    createEditorStateFromRaw(rawContentState)
  );
  const CommentControl = useMemo(
    () => getCommentControl(commentApp, contentPath, fieldNode),
    [commentApp, contentPath, fieldNode]
  );
  const commentsSelector = useMemo(
    () => commentApp.utils.selectCommentsForContentPathFactory(contentPath),
    [contentPath, commentApp]
  );
  const CommentDecorator = useMemo(() => getCommentDecorator(commentApp), [
    commentApp,
  ]);
  const comments = useSelector(commentsSelector, shallowEqual);
  const enabled = useSelector(commentApp.selectors.selectEnabled);
  const focusedId = useSelector(commentApp.selectors.selectFocused);

  const ids = useMemo(() => comments.map((comment) => comment.localId), [
    comments,
  ]);

  const commentStyles: Array<InlineStyle> = useMemo(
    () =>
      ids.map((id) => ({
        type: `${COMMENT_STYLE_IDENTIFIER}${id}`
      })),
    [ids]
  );

  const [uniqueStyleId, setUniqueStyleId] = useState(0);

  const previousFocused = usePrevious(focusedId);
  const previousIds = usePrevious(ids);
  const previousEnabled = usePrevious(enabled);
  useEffect(() => {
    // Only trigger a focus-related rerender if the current focused comment is inside the field, or the previous one was
    const validFocusChange =
      previousFocused !== focusedId &&
      ((previousFocused && previousIds && previousIds.includes(previousFocused)) ||
        focusedId && ids.includes(focusedId));

    if (
      !validFocusChange &&
      previousIds === ids &&
      previousEnabled === enabled
    ) {
      return;
    }

    // Filter out any invalid styles - deleted comments, or now unneeded STYLE_RERENDER forcing styles
    const filteredContent: ContentState = filterInlineStyles(
      inlineStyles
        .map((style) => style.type)
        .concat(ids.map((id) => `${COMMENT_STYLE_IDENTIFIER}${id}`)),
      editorState.getCurrentContent()
    );
    // Force reset the editor state to ensure redecoration, and apply a new (blank) inline style to force
    // inline style rerender. This must be entirely new for the rerender to trigger, hence the unique
    // style id, as with the undo stack we cannot guarantee that a previous style won't persist without
    // filtering everywhere, which seems a bit too heavyweight.
    // This hack can be removed when draft-js triggers inline style rerender on props change
    setEditorState((state) =>
      forceResetEditorState(
        state,
        Modifier.applyInlineStyle(
          filteredContent,
          getFullSelectionState(filteredContent),
          `STYLE_RERENDER_${uniqueStyleId}`
        )
      )
    );
    setUniqueStyleId((id) => (id + 1) % 200);
  }, [focusedId, enabled, inlineStyles, ids, editorState]);

  useEffect(() => {
    // if there are any comments without annotations, we need to add them to the EditorState
    let contentState = editorState.getCurrentContent();
    let hasUpdated = false;
    comments.filter(comment => !comment.annotation).forEach((comment) => {
      commentApp.updateAnnotation(new DraftailInlineAnnotation(fieldNode), comment.localId);
      const style = `${COMMENT_STYLE_IDENTIFIER}${comment.localId}`;
      try {
        const positions = JSON.parse(comment.position);
        positions.forEach((position) => {
          contentState = applyInlineStyleToRange({
            contentState,
            blockKey: position.key,
            start: position.start,
            end: position.end,
            style
          });
          hasUpdated = true;
        });
      } catch (err) {
        console.error(`Error loading comment position for comment ${comment.localId}`);
        console.error(err);
      }
    });
    if (hasUpdated) {
      setEditorState(forceResetEditorState(editorState, contentState));
    }
  }, [comments]);

  const timeoutRef = useRef<number | undefined>();
  useEffect(() => {
    // This replicates the onSave logic in Draftail, but only saves the state with all
    // comment styles filtered out
    window.clearTimeout(timeoutRef.current);
    const filteredEditorState = EditorState.push(
      editorState,
      filterInlineStyles(
        inlineStyles.map((style) => style.type),
        editorState.getCurrentContent()
      ),
      'change-inline-style'
    );
    timeoutRef.current = window.setTimeout(
      () => {
        onSave(serialiseEditorStateToRaw(filteredEditorState));

        // Next, update comment positions in the redux store
        updateCommentPositions({ editorState, comments, commentApp });
      },
      250
    );
    return () => {
      window.clearTimeout(timeoutRef.current);
    };
  }, [editorState, inlineStyles]);

  return (
    <DraftailEditor
      ref={editorRef}
      onChange={(state: EditorState) => {
        let newEditorState = state;
        if (['undo', 'redo'].includes(state.getLastChangeType())) {
          const filteredContent = filterInlineStyles(
            inlineStyles
              .map(style => style.type)
              .concat(ids.map(id => `${COMMENT_STYLE_IDENTIFIER}${id}`)),
            state.getCurrentContent()
          );
          newEditorState = forceResetEditorState(state, filteredContent);
        }
        setEditorState(newEditorState);
      }}
      editorState={editorState}
      controls={enabled ? [CommentControl] : []}
      decorators={
        enabled
          ? [
            {
              strategy: (
                block: ContentBlock, callback: (start: number, end: number) => void
              ) => findCommentStyleRanges(block, callback),
              component: CommentDecorator,
            },
          ]
          : []
      }
      inlineStyles={inlineStyles.concat(commentStyles)}
      plugins={enabled ? [{
        customStyleFn: (styleSet: DraftInlineStyle) => {
          // Use of casting in this function is due to issue #1563 in immutable-js, which causes operations like
          // map and filter to lose type information on the results. It should be fixed in v4: when we upgrade,
          // this casting should be removed
          const localCommentStyles = styleSet.filter(styleIsComment) as Immutable.OrderedSet<string>;
          const numStyles = localCommentStyles.count();
          if (numStyles > 0) {
            // There is at least one comment in the range
            const commentIds = localCommentStyles.map(
              style => getIdForCommentStyle(style as string)
            ) as unknown as Immutable.OrderedSet<number>;
            let background = standardHighlight;
            if (focusedId && commentIds.has(focusedId)) {
              // Use the focused colour if one of the comments is focused
              background = focusedHighlight;
              return {
                'background-color': background,
                'color': standardHighlight
              };
            } else if (numStyles > 1) {
              // Otherwise if we're in a region with overlapping comments, use a slightly darker colour than usual
              // to indicate that
              background = overlappingHighlight;
            }
            return {
              'background-color': background
            };
          }
          return undefined;
        }
      }] : []
      }
      {...options}
    />
  );
}

export default CommentableEditor;
