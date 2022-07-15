import {
  DraftailEditor,
  ToolbarButton,
  createEditorStateFromRaw,
  serialiseEditorStateToRaw,
  InlineStyleControl,
  ControlComponentProps,
  DraftailEditorProps,
} from 'draftail';
import {
  CharacterMetadata,
  ContentBlock,
  ContentState,
  DraftInlineStyle,
  EditorState,
  KeyBindingUtil,
  Modifier,
  RawDraftContentState,
  RichUtils,
  SelectionState,
} from 'draft-js';
import type { DraftEditorLeaf } from 'draft-js/lib/DraftEditorLeaf.react';
import { filterInlineStyles } from 'draftjs-filters';
import React, {
  MutableRefObject,
  ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useSelector, shallowEqual } from 'react-redux';
import type { Comment } from '../../CommentApp/state/comments';
import type { Annotation } from '../../CommentApp/utils/annotation';
import type { CommentApp } from '../../CommentApp/main';
import { gettext } from '../../../utils/gettext';

import Icon from '../../Icon/Icon';

const { isOptionKeyCommand } = KeyBindingUtil;

const COMMENT_STYLE_IDENTIFIER = 'COMMENT-';

// Hack taken from https://github.com/springload/draftail/blob/main/lib/api/behavior.js#L30
// Can be replaced with usesMacOSHeuristics once we upgrade draft-js
const IS_MAC_OS = isOptionKeyCommand({ altKey: true } as any) === true;

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
 * `getAnchorNode` is called by the comments app to determine which node
 * to float the comment alongside
 */
export class DraftailInlineAnnotation implements Annotation {
  /**
   * Create an inline annotation
   * @param {Element} field - an element to provide the fallback position for comments without any inline decorators
   */
  field: Element;
  decoratorRefs: Map<DecoratorRef, BlockKey>;
  focusedBlockKey: BlockKey;
  cachedMedianRef: DecoratorRef | null;

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
      (firstRef, secondRef) =>
        this.getHeightForRef(firstRef) - this.getHeightForRef(secondRef),
    );
    const length = refs.length;
    if (length > 0) {
      return refs[Math.ceil(length / 2 - 1)];
    }
    return null;
  }

  getTab() {
    return this.field.closest('[role="tabpanel"]')?.getAttribute('id');
  }

  getAnchorNode(focused = false) {
    // The comment should always aim to float by an annotation, rather than between them
    // so calculate which annotation is the median one by height and float the comment by that
    let medianRef: null | DecoratorRef = null;
    if (focused) {
      // If the comment is focused, calculate the median of refs only
      // within the focused block, to ensure the comment is visible
      // if the highlight has somehow been split up
      medianRef = DraftailInlineAnnotation.getMedianRef(
        Array.from(this.decoratorRefs.keys()).filter(
          (ref) => this.decoratorRefs.get(ref) === this.focusedBlockKey,
        ),
      );
    } else if (!this.cachedMedianRef) {
      // Our cache is empty - try to update it
      medianRef = DraftailInlineAnnotation.getMedianRef(
        Array.from(this.decoratorRefs.keys()),
      );
      this.cachedMedianRef = medianRef;
    } else {
      // Use the cached median refs
      medianRef = this.cachedMedianRef;
    }

    // Fallback to the field node, if the comment has no decorator refs
    return medianRef?.current || this.field;
  }
}

function applyInlineStyleToRange({
  contentState,
  style,
  blockKey,
  start,
  end,
}: {
  contentState: ContentState;
  style: string;
  blockKey: BlockKey;
  start: number;
  end: number;
}) {
  return Modifier.applyInlineStyle(
    contentState,
    new SelectionState({
      anchorKey: blockKey,
      anchorOffset: start,
      focusKey: blockKey,
      focusOffset: end,
    }),
    style,
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
    focusOffset: lastBlock.getLength(),
  });
}

function addNewComment(
  editorState: EditorState,
  fieldNode: Element,
  commentApp: CommentApp,
  contentPath: string,
) {
  let state = editorState;
  const annotation = new DraftailInlineAnnotation(fieldNode);
  const commentId = commentApp.makeComment(annotation, contentPath, '[]');
  const selection = editorState.getSelection();
  // If the selection is collapsed, add the comment highlight on the whole field
  state = EditorState.acceptSelection(
    editorState,
    selection.isCollapsed()
      ? getFullSelectionState(editorState.getCurrentContent())
      : selection,
  );

  return EditorState.acceptSelection(
    RichUtils.toggleInlineStyle(
      state,
      `${COMMENT_STYLE_IDENTIFIER}${commentId}`,
    ),
    selection,
  );
}

function styleIsComment(style: string | undefined): style is string {
  return style !== undefined && style.startsWith(COMMENT_STYLE_IDENTIFIER);
}

function getIdForCommentStyle(style: string) {
  return parseInt(style.slice(COMMENT_STYLE_IDENTIFIER.length), 10);
}

function getCommentPositions(editorState: EditorState) {
  // Construct a map of comment id -> array of style ranges
  const commentPositions = new Map();

  editorState
    .getCurrentContent()
    .getBlocksAsArray()
    .forEach((block) => {
      const key = block.getKey();
      block.findStyleRanges(
        (metadata) => metadata.getStyle().some(styleIsComment),
        (start, end) => {
          block
            .getInlineStyleAt(start)
            .filter(styleIsComment)
            .forEach((style) => {
              // We have already filtered out any undefined styles, so cast here
              const id = getIdForCommentStyle(style as string);
              let existingPosition = commentPositions.get(id);
              if (!existingPosition) {
                existingPosition = [];
              }
              existingPosition.push({
                key: key,
                start: start,
                end: end,
              });
              commentPositions.set(id, existingPosition);
            });
        },
      );
    });
  return commentPositions;
}

function createFromBlockArrayOrPlaceholder(blockArray: ContentBlock[]) {
  // This is needed due to (similar) https://github.com/facebook/draft-js/issues/1660
  // Causing empty block arrays in an editorState to crash the editor
  // It is fixed in later versions of draft-js (~11.3?), but this upgrade needs
  // more evaluation for impact on Draftail/Commenting/other Wagtail usages
  // TODO: upgrade Draft.js
  if (blockArray.length > 0) {
    return ContentState.createFromBlockArray(blockArray);
  }
  return ContentState.createFromText(' ');
}

export function splitState(editorState: EditorState) {
  const selection = editorState.getSelection();
  const anchorKey = selection.getAnchorKey();
  const currentContent = editorState.getCurrentContent();

  // In order to use Modifier.splitBlock, we need a collapsed selection
  // otherwise we will lose highlighted text
  const collapsedSelection = selection.isCollapsed()
    ? selection
    : new SelectionState({
        anchorKey: selection.getStartKey(),
        anchorOffset: selection.getStartOffset(),
        focusKey: selection.getStartKey(),
        focusOffset: selection.getStartOffset(),
      });

  const multipleBlockContent = Modifier.splitBlock(
    currentContent,
    collapsedSelection,
  ).getBlocksAsArray();
  const index = multipleBlockContent.findIndex(
    (block) => block.getKey() === anchorKey,
  );
  const blocksBefore = multipleBlockContent.slice(0, index + 1);
  const blocksAfter = multipleBlockContent.slice(index + 1);
  const stateBefore = EditorState.push(
    editorState,
    createFromBlockArrayOrPlaceholder(blocksBefore),
    'remove-range',
  );
  const stateAfter = EditorState.push(
    editorState,
    createFromBlockArrayOrPlaceholder(blocksAfter),
    'remove-range',
  );

  const commentIdsToMove = new Set(getCommentPositions(stateAfter).keys());
  return {
    stateBefore,
    stateAfter,
    shouldMoveCommentFn: (comment: Comment) =>
      commentIdsToMove.has(comment.localId),
  };
}

export function getSplitControl(
  splitFn: (
    stateBefore: EditorState,
    stateAfter: EditorState,
    shouldMoveCommentFn: (comment: Comment) => boolean,
  ) => void,
  enabled = true,
) {
  const title = gettext('Split block');
  const name = 'split';
  const icon = <Icon name="cut" />;
  if (!enabled) {
    // Taken from https://github.com/springload/draftail/blob/main/lib/components/ToolbarButton.js#L65
    // as it doesn't take the disabled prop
    return () => (
      <button
        name={name}
        className="Draftail-ToolbarButton"
        type="button"
        aria-label={title}
        data-draftail-balloon={title}
        tabIndex={-1}
        disabled={true}
      >
        {icon}
      </button>
    );
  }
  return ({ getEditorState }: ControlComponentProps) => (
    <ToolbarButton
      name={name}
      active={false}
      title={title}
      icon={icon}
      onClick={() => {
        const result = splitState(getEditorState());
        if (result) {
          splitFn(
            result.stateBefore,
            result.stateAfter,
            result.shouldMoveCommentFn,
          );
        }
      }}
    />
  );
}

function getCommentControl(
  commentApp: CommentApp,
  contentPath: string,
  fieldNode: Element,
) {
  return ({ getEditorState, onChange }: ControlComponentProps) => (
    <span className="Draftail-CommentControl" data-comment-add>
      <ToolbarButton
        name="comment"
        active={false}
        title={`${gettext('Add a comment')}\n${
          IS_MAC_OS ? '⌘ + Alt + M' : 'Ctrl + Alt + M'
        }`}
        icon={
          <>
            <Icon name="comment-add" />
            <Icon name="comment-add-reversed" />
          </>
        }
        onClick={() => {
          onChange(
            addNewComment(getEditorState(), fieldNode, commentApp, contentPath),
          );
        }}
      />
    </span>
  );
}

function findCommentStyleRanges(
  contentBlock: ContentBlock,
  callback: (start: number, end: number) => void,
  filterFn?: (metadata: CharacterMetadata) => boolean,
) {
  // Find comment style ranges that do not overlap an existing entity
  const filterFunction =
    filterFn ||
    ((metadata: CharacterMetadata) => metadata.getStyle().some(styleIsComment));
  const entityRanges: Array<[number, number]> = [];
  contentBlock.findEntityRanges(
    (character) => character.getEntity() !== null,
    (start, end) => entityRanges.push([start, end]),
  );
  contentBlock.findStyleRanges(filterFunction, (start, end) => {
    const interferingEntityRanges = entityRanges
      .filter((value) => value[1] > start)
      .filter((value) => value[0] < end);
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
  });
}

export function updateCommentPositions({
  editorState,
  comments,
  commentApp,
}: {
  editorState: EditorState;
  comments: Array<Comment>;
  commentApp: CommentApp;
}) {
  const commentPositions = getCommentPositions(editorState);

  comments
    .filter((comment) => comment.annotation)
    .forEach((comment) => {
      // if a comment has an annotation - ie the field has it inserted - update its position
      const newPosition = commentPositions.get(comment.localId);
      const serializedNewPosition = newPosition
        ? JSON.stringify(newPosition)
        : '[]';
      if (comment.position !== serializedNewPosition) {
        commentApp.store.dispatch(
          commentApp.actions.updateComment(comment.localId, {
            position: serializedNewPosition,
          }),
        );
      }
    });
}

/**
 * Given a contentBlock and offset within it, find the id of the comment at that offset which
 * has the fewest style ranges within the block, or null if no comment exists at the offset
 */
export function findLeastCommonCommentId(block: ContentBlock, offset: number) {
  const styles = block
    .getInlineStyleAt(offset)
    .filter(styleIsComment) as Immutable.OrderedSet<string>;
  let styleToUse: string;
  const styleCount = styles.count();
  if (styleCount === 0) {
    return null;
  } else if (styleCount > 1) {
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
      findCommentStyleRanges(
        block,
        () => {
          counter += 1;
        },
        (metadata) =>
          metadata.getStyle().some((rangeStyle) => rangeStyle === style),
      );
      return [style, counter];
    }) as unknown as Immutable.OrderedSet<[string, number]>;

    styleFreq = styleFreq.sort(
      (firstStyleCount, secondStyleCount) =>
        firstStyleCount[1] - secondStyleCount[1],
    ) as Immutable.OrderedSet<[string, number]>;

    styleToUse = styleFreq.first()[0];
  } else {
    styleToUse = styles.first();
  }
  return getIdForCommentStyle(styleToUse);
}

interface DecoratorProps {
  contentState: ContentState;
  children?: Array<DraftEditorLeaf>;
}

function getCommentDecorator(commentApp: CommentApp) {
  const CommentDecorator = ({ contentState, children }: DecoratorProps) => {
    // The comment decorator makes a comment clickable, allowing it to be focused.
    // It does not provide styling, as draft-js imposes a 1 decorator/string limit,
    // which would prevent comment highlights going over links/other entities
    if (!children) {
      return null;
    }

    const enabled = useSelector(commentApp.selectors.selectEnabled);
    const blockKey: BlockKey = children[0].props.block.getKey();
    const start: number = children[0].props.start;

    const commentId = useMemo(() => {
      const block = contentState.getBlockForKey(blockKey);
      return findLeastCommonCommentId(block, start);
    }, [blockKey, start]);
    const annotationNode = useRef(null);
    useEffect(() => {
      // Add a ref to the annotation, allowing the comment to float alongside the attached text.
      // This adds rather than sets the ref, so that a comment may be attached across paragraphs or around entities
      if (!commentId) {
        return undefined;
      }
      const annotation = commentApp.layout.commentAnnotations.get(commentId);
      if (annotation && annotation instanceof DraftailInlineAnnotation) {
        annotation.addDecoratorRef(annotationNode, blockKey);
        return () => annotation.removeDecoratorRef(annotationNode);
      }
      return undefined; // eslint demands an explicit return here
    }, [commentId, annotationNode, blockKey]);

    if (!enabled) {
      return children;
    }

    const onClick = () => {
      // Ensure the comment will appear alongside the current block
      if (!commentId) {
        return;
      }
      const annotation = commentApp.layout.commentAnnotations.get(commentId);
      if (
        annotation &&
        annotation instanceof DraftailInlineAnnotation &&
        annotationNode
      ) {
        annotation.setFocusedBlockKey(blockKey);
      }

      // Pin and focus the clicked comment
      commentApp.store.dispatch(
        commentApp.actions.setFocusedComment(commentId, {
          updatePinnedComment: true,
          forceFocus: false,
        }),
      );
    };
    return (
      <span
        role="button"
        ref={annotationNode}
        onClick={onClick}
        aria-label={gettext('Focus comment')}
        data-annotation
      >
        {children}
      </span>
    );
  };
  return CommentDecorator;
}

function forceResetEditorState(
  editorState: EditorState,
  replacementContent?: ContentState,
) {
  const content = replacementContent || editorState.getCurrentContent();
  const state = EditorState.set(
    EditorState.createWithContent(content, editorState.getDecorator()),
    {
      selection: editorState.getSelection(),
      undoStack: editorState.getUndoStack(),
      redoStack: editorState.getRedoStack(),
      inlineStyleOverride: editorState.getInlineStyleOverride(),
    },
  );
  return EditorState.acceptSelection(state, state.getSelection());
}

export function addCommentsToEditor(
  contentState: ContentState,
  comments: Comment[],
  commentApp: CommentApp,
  getAnnotation: () => Annotation,
) {
  let newContentState = contentState;
  comments
    .filter((comment) => !comment.annotation)
    .forEach((comment) => {
      commentApp.updateAnnotation(getAnnotation(), comment.localId);
      const style = `${COMMENT_STYLE_IDENTIFIER}${comment.localId}`;
      try {
        const positions = JSON.parse(comment.position);
        positions.forEach((position) => {
          newContentState = applyInlineStyleToRange({
            contentState: newContentState,
            blockKey: position.key,
            start: position.start,
            end: position.end,
            style,
          });
        });
      } catch (err) {
        /* eslint-disable no-console */
        console.error(
          `Error loading comment position for comment ${comment.localId}`,
        );
        console.error(err);
        /* esline-enable no-console */
      }
    });
  return newContentState;
}

type Direction = 'RTL' | 'LTR';

function handleArrowAtContentEnd(
  state: EditorState,
  setEditorState: (newState: EditorState) => void,
  direction: Direction,
) {
  // If at the end of content and pressing in the same direction as the text, remove the comment style from
  // further typing
  const newState = state;
  const selection = newState.getSelection();
  const lastBlock = newState.getCurrentContent().getLastBlock();
  const textDirection = newState.getDirectionMap().get(lastBlock.getKey());

  if (
    !(
      textDirection === direction &&
      selection.isCollapsed() &&
      selection.getAnchorKey() === lastBlock.getKey() &&
      selection.getAnchorOffset() === lastBlock.getLength()
    )
  ) {
    return;
  }
  setEditorState(
    EditorState.setInlineStyleOverride(
      newState,
      newState
        .getCurrentInlineStyle()
        .filter((style) => !styleIsComment(style)) as DraftInlineStyle,
    ),
  );
}

interface ColorConfigProp {
  standardHighlight: string;
  overlappingHighlight: string;
  focusedHighlight: string;
}

interface CommentableEditorProps {
  commentApp: CommentApp;
  fieldNode: Element;
  contentPath: string;
  rawContentState: RawDraftContentState;
  onSave: (rawContent: RawDraftContentState | null) => void;
  inlineStyles: InlineStyleControl[];
  editorRef: (editor: ReactNode) => void;
  colorConfig: ColorConfigProp;
  isCommentShortcut: (e: React.KeyboardEvent) => boolean;
  // Unfortunately the EditorPlugin type isn't exported in our version of 'draft-js-plugins-editor'
  plugins?: Record<string, unknown>[];
  controls?: DraftailEditorProps['controls'];
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
  isCommentShortcut,
  plugins = [],
  controls = [],
  ...options
}: CommentableEditorProps) {
  const [editorState, setEditorState] = useState(() =>
    createEditorStateFromRaw(rawContentState),
  );
  const CommentControl = useMemo(
    () => getCommentControl(commentApp, contentPath, fieldNode),
    [commentApp, contentPath, fieldNode],
  );
  const commentsSelector = useMemo(
    () => commentApp.utils.selectCommentsForContentPathFactory(contentPath),
    [contentPath, commentApp],
  );
  const CommentDecorator = useMemo(
    () => getCommentDecorator(commentApp),
    [commentApp],
  );
  const comments = useSelector(commentsSelector, shallowEqual);
  const enabled = useSelector(commentApp.selectors.selectEnabled);
  const focusedId = useSelector(commentApp.selectors.selectFocused);

  const ids = useMemo(
    () => comments.map((comment) => comment.localId),
    [comments],
  );

  const commentStyles: InlineStyleControl[] = useMemo(
    () =>
      ids.map((id) => ({
        type: `${COMMENT_STYLE_IDENTIFIER}${id}`,
      })),
    [ids],
  );

  const [uniqueStyleId, setUniqueStyleId] = useState(0);

  const previousFocused = usePrevious(focusedId);
  const previousIds = usePrevious(ids);
  const previousEnabled = usePrevious(enabled);
  useEffect(() => {
    // Only trigger a focus-related rerender if the current focused comment is inside the field, or the previous one was
    const validFocusChange =
      previousFocused !== focusedId &&
      ((previousFocused &&
        previousIds &&
        previousIds.includes(previousFocused)) ||
        (focusedId && ids.includes(focusedId)));

    if (
      !validFocusChange &&
      previousEnabled === enabled &&
      (previousIds === ids ||
        (previousIds.length === ids.length &&
          previousIds.every((value, index) => value === ids[index])))
    ) {
      return;
    }

    // Filter out any invalid styles - deleted comments, or now unneeded STYLE_RERENDER forcing styles
    const filteredContent: ContentState = filterInlineStyles(
      inlineStyles
        .map((style) => style.type)
        .concat(ids.map((id) => `${COMMENT_STYLE_IDENTIFIER}${id}`)),
      editorState.getCurrentContent(),
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
          `STYLE_RERENDER_${uniqueStyleId}`,
        ),
      ),
    );
    setUniqueStyleId((id) => (id + 1) % 200);
  }, [focusedId, enabled, inlineStyles, ids, editorState]);

  useEffect(() => {
    // if there are any comments without annotations, we need to add them to the EditorState
    const contentState = editorState.getCurrentContent();
    const newContentState = addCommentsToEditor(
      contentState,
      comments,
      commentApp,
      () => new DraftailInlineAnnotation(fieldNode),
    );
    if (contentState !== newContentState) {
      setEditorState(forceResetEditorState(editorState, newContentState));
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
        editorState.getCurrentContent(),
      ),
      'change-inline-style',
    );
    timeoutRef.current = window.setTimeout(() => {
      onSave(serialiseEditorStateToRaw(filteredEditorState));

      // Next, update comment positions in the redux store
      updateCommentPositions({ editorState, comments, commentApp });
    }, 250);
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
              .map((style) => style.type)
              .concat(ids.map((id) => `${COMMENT_STYLE_IDENTIFIER}${id}`)),
            state.getCurrentContent(),
          );
          newEditorState = forceResetEditorState(state, filteredContent);
        } else if (state.getLastChangeType() === 'split-block') {
          const content = newEditorState.getCurrentContent();
          const selection = newEditorState.getSelection();
          const style = content
            .getBlockForKey(selection.getAnchorKey())
            .getInlineStyleAt(selection.getAnchorOffset());
          // If starting a new paragraph (and not splitting an existing comment)
          // ensure any new text entered doesn't get a comment style
          if (!style.some((styleName) => styleIsComment(styleName))) {
            newEditorState = EditorState.setInlineStyleOverride(
              newEditorState,
              newEditorState
                .getCurrentInlineStyle()
                .filter(
                  (styleName) => !styleIsComment(styleName),
                ) as DraftInlineStyle,
            );
          }
        }
        setEditorState(newEditorState);
      }}
      editorState={editorState}
      controls={
        enabled ? controls.concat([{ block: CommentControl }]) : controls
      }
      inlineStyles={inlineStyles.concat(commentStyles)}
      plugins={plugins.concat([
        {
          decorators: [
            {
              strategy: (
                block: ContentBlock,
                callback: (start: number, end: number) => void,
              ) => findCommentStyleRanges(block, callback),
              component: CommentDecorator,
            },
          ],
          keyBindingFn: (e: React.KeyboardEvent) => {
            if (isCommentShortcut(e)) {
              return 'comment';
            }
            return undefined;
          },
          onRightArrow: (_: React.KeyboardEvent, { getEditorState }) => {
            // In later versions of draft-js, this is deprecated and can be handled via handleKeyCommand instead
            // when draftail upgrades, this logic can be moved there

            handleArrowAtContentEnd(getEditorState(), setEditorState, 'LTR');
          },
          onLeftArrow: (_: React.KeyboardEvent, { getEditorState }) => {
            // In later versions of draft-js, this is deprecated and can be handled via handleKeyCommand instead
            // when draftail upgrades, this logic can be moved there

            handleArrowAtContentEnd(getEditorState(), setEditorState, 'RTL');
          },
          handleKeyCommand: (command: string, state: EditorState) => {
            if (enabled && command === 'comment') {
              const selection = state.getSelection();
              const content = state.getCurrentContent();
              if (selection.isCollapsed()) {
                // We might be trying to focus an existing comment - check if we're in a comment range
                const id = findLeastCommonCommentId(
                  content.getBlockForKey(selection.getAnchorKey()),
                  selection.getAnchorOffset(),
                );
                if (id) {
                  // Focus the comment
                  commentApp.store.dispatch(
                    commentApp.actions.setFocusedComment(id, {
                      updatePinnedComment: true,
                      forceFocus: true,
                    }),
                  );
                  return 'handled';
                }
              }
              // Otherwise, add a new comment
              setEditorState(
                addNewComment(state, fieldNode, commentApp, contentPath),
              );
              return 'handled';
            }
            return 'not-handled';
          },
          customStyleFn: (styleSet: DraftInlineStyle) => {
            if (!enabled) {
              return undefined;
            }
            // Use of casting in this function is due to issue #1563 in immutable-js, which causes operations like
            // map and filter to lose type information on the results. It should be fixed in v4: when we upgrade,
            // this casting should be removed
            const localCommentStyles = styleSet.filter(
              styleIsComment,
            ) as Immutable.OrderedSet<string>;
            const numStyles = localCommentStyles.count();
            if (numStyles > 0) {
              // There is at least one comment in the range
              const commentIds = localCommentStyles.map((style) =>
                getIdForCommentStyle(style as string),
              ) as unknown as Immutable.OrderedSet<number>;
              let background = standardHighlight;
              if (focusedId && commentIds.has(focusedId)) {
                // Use the focused colour if one of the comments is focused
                background = focusedHighlight;
                return {
                  'background-color': background,
                  'color': standardHighlight,
                };
              } else if (numStyles > 1) {
                // Otherwise if we're in a region with overlapping comments, use a slightly darker colour than usual
                // to indicate that
                background = overlappingHighlight;
              }
              return {
                'background-color': background,
              };
            }
            return undefined;
          },
        },
      ])}
      {...options}
    />
  );
}

export default CommentableEditor;
