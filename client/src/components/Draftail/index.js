import React from 'react';
import ReactDOM from 'react-dom';
import { DraftailEditor } from 'draftail';
import { Provider } from 'react-redux';

import { IS_IE11, STRINGS } from '../../config/wagtailConfig';

import Icon from '../Icon/Icon';

export { default as Link } from './decorators/Link';
export { default as Document } from './decorators/Document';
export { default as ImageBlock } from './blocks/ImageBlock';
export { default as EmbedBlock } from './blocks/EmbedBlock';

import {
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource
} from './sources/ModalWorkflowSource';
import Tooltip from './Tooltip/Tooltip';
import TooltipEntity from './decorators/TooltipEntity';
import EditorFallback from './EditorFallback/EditorFallback';
import CommentableEditor from './CommentableEditor/CommentableEditor';

// 1024x1024 SVG path rendering of the "↵" character, that renders badly in MS Edge.
const BR_ICON = 'M.436 633.471l296.897-296.898v241.823h616.586V94.117h109.517v593.796H297.333v242.456z';

/**
 * Registry for client-side code of Draftail plugins.
 */
const PLUGINS = {};

const registerPlugin = (plugin) => {
  PLUGINS[plugin.type] = plugin;
  return PLUGINS;
};

/**
 * Wraps a style/block/entity type’s icon with an icon font implementation,
 * so Draftail can use icon fonts in its toolbar.
 */
export const wrapWagtailIcon = type => {
  const isIconFont = type.icon && typeof type.icon === 'string';
  if (isIconFont) {
    return Object.assign(type, {
      icon: <Icon name={type.icon} />,
    });
  }

  return type;
};

/**
 * Initialises the DraftailEditor for a given field.
 * @param {string} selector
 * @param {Object} options
 * @param {Element} currentScript
 */
const initEditor = (selector, options, currentScript) => {
  // document.currentScript is not available in IE11. Use a fallback instead.
  const context = currentScript ? currentScript.parentNode : document.body;
  // If the field is not in the current context, look for it in the whole body.
  // Fallback for sequence.js jQuery eval-ed scripts running in document.head.
  const field = context.querySelector(selector) || document.body.querySelector(selector);

  const editorWrapper = document.createElement('div');
  editorWrapper.className = 'Draftail-Editor__wrapper';
  editorWrapper.setAttribute('data-draftail-editor-wrapper', true);

  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = rawContentState => {
    field.rawContentState = rawContentState;
    field.value = JSON.stringify(rawContentState);
  };

  const blockTypes = options.blockTypes || [];
  const inlineStyles = options.inlineStyles || [];
  let entityTypes = options.entityTypes || [];

  entityTypes = entityTypes.map(wrapWagtailIcon).map((type) => {
    const plugin = PLUGINS[type.type];

    // Override the properties defined in the JS plugin: Python should be the source of truth.
    return Object.assign({}, plugin, type);
  });

  const enableHorizontalRule = options.enableHorizontalRule ? {
    description: STRINGS.HORIZONTAL_LINE,
  } : false;

  const rawContentState = JSON.parse(field.value);
  field.rawContentState = rawContentState;

  const editorRef = (ref) => {
    // Bind editor instance to its field so it can be accessed imperatively elsewhere.
    field.draftailEditor = ref;
  };

  const sharedProps = {
    rawContentState: rawContentState,
    onSave: serialiseInputValue,
    placeholder: STRINGS.WRITE_HERE,
    spellCheck: true,
    enableLineBreak: {
      description: STRINGS.LINE_BREAK,
      icon: BR_ICON,
    },
    showUndoControl: { description: STRINGS.UNDO },
    showRedoControl: { description: STRINGS.REDO },
    maxListNesting: 4,
    // Draft.js + IE 11 presents some issues with pasting rich text. Disable rich paste there.
    stripPastedStyles: IS_IE11,
    ...options,
    blockTypes: blockTypes.map(wrapWagtailIcon),
    inlineStyles: inlineStyles.map(wrapWagtailIcon),
    entityTypes,
    enableHorizontalRule
  };

  const styles = getComputedStyle(document.documentElement);
  const colors = {
    standardHighlight: styles.getPropertyValue('--color-primary-light'),
    overlappingHighlight: styles.getPropertyValue('--color-primary-lighter'),
    focusedHighlight: styles.getPropertyValue('--color-primary')
  };

  // If the field has a valid contentpath - ie is not an InlinePanel or under a ListBlock -
  // and the comments system is initialized then use CommentableEditor, otherwise plain DraftailEditor
  const contentPath = window.comments?.getContentPath(field) || '';
  const editor = (window.comments?.commentApp && contentPath !== '') ?
    <Provider store={window.comments.commentApp.store}>
      <CommentableEditor
        editorRef={editorRef}
        commentApp={window.comments.commentApp}
        fieldNode={field.parentNode}
        contentPath={contentPath}
        colorConfig={colors}
        isCommentShortcut={window.comments.isCommentShortcut}
        {...sharedProps}
      />
    </Provider>
    : <DraftailEditor
      ref={editorRef}
      {...sharedProps}
    />;

  ReactDOM.render(<EditorFallback field={field}>{editor}</EditorFallback>, editorWrapper);
};

export default {
  initEditor,
  registerPlugin,
  // Components exposed for third-party reuse.
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
  Tooltip,
  TooltipEntity,
};
