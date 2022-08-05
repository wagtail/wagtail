import React from 'react';
import ReactDOM from 'react-dom';
import {
  DraftailEditor,
  InlineToolbar,
  MetaToolbar,
  CommandPalette,
  DraftUtils,
} from 'draftail';
import { Provider } from 'react-redux';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

import {
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
} from './sources/ModalWorkflowSource';
import Tooltip from './Tooltip/Tooltip';
import TooltipEntity from './decorators/TooltipEntity';
import MaxLength from './controls/MaxLength';
import EditorFallback from './EditorFallback/EditorFallback';
import CommentableEditor, {
  getSplitControl,
  splitState,
} from './CommentableEditor/CommentableEditor';

export { default as Link, onPasteLink } from './decorators/Link';
export { default as Document } from './decorators/Document';
export { default as ImageBlock } from './blocks/ImageBlock';
export { default as EmbedBlock } from './blocks/EmbedBlock';

// 1024x1024 SVG path rendering of the "↵" character, that renders badly in MS Edge.
const BR_ICON =
  'M.436 633.471l296.897-296.898v241.823h616.586V94.117h109.517v593.796H297.333v242.456z';

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
export const wrapWagtailIcon = (type) => {
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
 * @param {Object} originalOptions
 * @param {Element} currentScript
 */
const initEditor = (selector, originalOptions, currentScript) => {
  // document.currentScript is not available in IE11. Use a fallback instead.
  const context = currentScript ? currentScript.parentNode : document.body;
  // If the field is not in the current context, look for it in the whole body.
  // Fallback for sequence.js jQuery eval-ed scripts running in document.head.
  const field =
    context.querySelector(selector) || document.body.querySelector(selector);

  const editorWrapper = document.createElement('div');
  editorWrapper.className = 'Draftail-Editor__wrapper';
  editorWrapper.setAttribute('data-draftail-editor-wrapper', true);

  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = (rawContentState) => {
    field.rawContentState = rawContentState;
    field.value = JSON.stringify(rawContentState);
  };

  const rawContentState = JSON.parse(field.value);
  field.rawContentState = rawContentState;

  const editorRef = (ref) => {
    // Bind editor instance to its field so it can be accessed imperatively elsewhere.
    field.draftailEditor = ref;
  };

  const getSharedPropsFromOptions = (newOptions) => {
    let ariaDescribedBy = null;
    const enableHorizontalRule = newOptions.enableHorizontalRule
      ? {
          description: gettext('Horizontal line'),
        }
      : false;

    const blockTypes = newOptions.blockTypes || [];
    const inlineStyles = newOptions.inlineStyles || [];
    let controls = newOptions.controls || [];
    const commands = newOptions.commands || true;
    let entityTypes = newOptions.entityTypes || [];

    entityTypes = entityTypes.map(wrapWagtailIcon).map((type) => {
      const plugin = PLUGINS[type.type];

      // Override the properties defined in the JS plugin: Python should be the source of truth.
      return { ...plugin, ...type };
    });

    // Only initialise the character count / max length on fields explicitly requiring it.
    if (field.hasAttribute('maxlength')) {
      const maxLengthID = `${field.id}-length`;
      ariaDescribedBy = maxLengthID;
      controls = controls.concat([
        {
          meta: (props) => (
            <MaxLength
              {...props}
              maxLength={field.maxLength}
              id={maxLengthID}
            />
          ),
        },
      ]);
    }

    return {
      rawContentState: rawContentState,
      onSave: serialiseInputValue,
      placeholder: gettext('Write something or type ‘/’ to insert a block'),
      spellCheck: true,
      enableLineBreak: {
        description: gettext('Line break'),
        icon: BR_ICON,
      },
      topToolbar: InlineToolbar,
      bottomToolbar: MetaToolbar,
      commandPalette: (props) => (
        <CommandPalette {...props} noResultsText={gettext('No results')} />
      ),
      maxListNesting: 4,
      stripPastedStyles: false,
      ariaDescribedBy,
      ...newOptions,
      blockTypes: blockTypes.map(wrapWagtailIcon),
      inlineStyles: inlineStyles.map(wrapWagtailIcon),
      entityTypes,
      controls,
      commands,
      enableHorizontalRule,
    };
  };

  const styles = getComputedStyle(document.documentElement);
  const colors = {
    standardHighlight: styles.getPropertyValue('--w-color-secondary-100'),
    overlappingHighlight: styles.getPropertyValue('--w-color-secondary-50'),
    focusedHighlight: styles.getPropertyValue('--w-color-secondary'),
  };

  let options;
  let setOptions = (newOptions) => {
    Object.assign(originalOptions, newOptions);
  };
  const DynamicOptionsEditorWrapper = ({
    initialOptions,
    contentPath,
    commentApp,
  }) => {
    [options, setOptions] = React.useState({ ...initialOptions });

    // If the field has a valid contentpath - ie is not an InlinePanel or under a ListBlock -
    // and the comments system is initialized then use CommentableEditor, otherwise plain DraftailEditor
    const sharedProps = getSharedPropsFromOptions(options);
    const editor =
      commentApp && contentPath !== '' ? (
        <Provider store={commentApp.store}>
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
      ) : (
        <DraftailEditor ref={editorRef} {...sharedProps} />
      );
    return editor;
  };

  ReactDOM.render(
    <EditorFallback field={field}>
      <DynamicOptionsEditorWrapper
        initialOptions={originalOptions}
        contentPath={window.comments?.getContentPath(field) || ''}
        commentApp={window.comments?.commentApp}
      />
    </EditorFallback>,
    editorWrapper,
  );

  return [options, setOptions];
};

export default {
  initEditor,
  getSplitControl,
  splitState,
  registerPlugin,
  DraftUtils,
  // Components exposed for third-party reuse.
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
  Tooltip,
  TooltipEntity,
};
