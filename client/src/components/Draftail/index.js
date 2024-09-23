import React from 'react';
import ReactDOM from 'react-dom';
import {
  DraftailEditor,
  BlockToolbar,
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
import ComboBox, {
  comboBoxLabel,
  comboBoxNoResults,
  comboBoxTriggerLabel,
} from '../ComboBox/ComboBox';
import CommentableEditor, {
  splitState,
} from './CommentableEditor/CommentableEditor';

export { default as Link, onPasteLink } from './decorators/Link';
export { default as Document } from './decorators/Document';
export { default as ImageBlock } from './blocks/ImageBlock';
export { default as EmbedBlock } from './blocks/EmbedBlock';

// 1024x1024 SVG path rendering of the "↵" character, that renders badly in MS Edge.
const BR_ICON =
  'M.436 633.471l296.897-296.898v241.823h616.586V94.117h109.517v593.796H297.333v242.456z';
const HR_ICON = <Icon name="minus" />;
const ADD_ICON = <Icon name="plus" />;

const pinButton = {
  floatingIcon: <Icon name="thumbtack" />,
  stickyIcon: <Icon name="thumbtack-crossed" />,
  floatingDescription: gettext('Pin toolbar'),
  stickyDescription: gettext('Unpin toolbar'),
};

const getSavedToolbar = () => {
  let saved = 'floating';
  try {
    saved = localStorage.getItem('wagtail:draftail-toolbar') || saved;
  } catch {
    // Use the default if localStorage isn’t available.
  }
  return saved;
};

/**
 * Scroll to keep the field on the same spot when switching toolbars,
 * and save the choice in localStorage.
 */
const onSetToolbar = (choice, callback) => {
  const activeEditor = document.activeElement;
  const before = activeEditor.getBoundingClientRect().top;
  callback(choice);

  // Delay scrolling until reflow has been fully computed.
  requestAnimationFrame(() => {
    const after = activeEditor.getBoundingClientRect().top;
    const scrollArea = document.querySelector('#main');
    scrollArea.scrollBy({
      // Scroll by a positive amount if the editor moved down, negative if up.
      top: after - before,
      behavior: 'instant',
    });
  });
  try {
    localStorage.setItem('wagtail:draftail-toolbar', choice);
  } catch {
    // Skip saving the preference if localStorage isn’t available.
  }
};

/**
 * Registry for client-side code of Draftail plugins.
 */
const PLUGINS = {
  entityTypes: {},
  plugins: {},
  controls: {},
  decorators: {},
};

/**
 * Client-side editor-specific equivalent to register_editor_plugin.
 * `optionName` defaults to entityTypes for backwards-compatibility with
 * previous function signature only allowing registering entities.
 */
const registerPlugin = (type, optionName = 'entityTypes') => {
  PLUGINS[optionName][type.type] = type;
  return PLUGINS[optionName];
};

/**
 * Wraps a style/block/entity type’s icon identifier with an icon component.
 */
export const wrapWagtailIcon = (type) => {
  const isNamedIcon = type.icon && typeof type.icon === 'string';
  if (isNamedIcon) {
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
          icon: HR_ICON,
        }
      : false;

    const blockTypes = newOptions.blockTypes || [];
    const inlineStyles = newOptions.inlineStyles || [];
    let controls = newOptions.controls || [];
    let decorators = newOptions.decorators || [];
    let plugins = newOptions.plugins || [];
    const commands = newOptions.commands || true;
    let entityTypes = newOptions.entityTypes || [];

    entityTypes = entityTypes
      .map(wrapWagtailIcon)
      // Override the properties defined in the JS plugin: Python should be the source of truth.
      .map((type) => ({ ...PLUGINS.entityTypes[type.type], ...type }));

    controls = controls.map((type) => ({
      ...PLUGINS.controls[type.type],
      ...type,
    }));
    decorators = decorators.map((type) => ({
      ...PLUGINS.decorators[type.type],
      ...type,
    }));
    plugins = plugins.map((type) => ({
      ...PLUGINS.plugins[type.type],
      ...type,
    }));

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
      topToolbar: (props) => (
        <>
          <BlockToolbar
            {...props}
            triggerIcon={ADD_ICON}
            triggerLabel={comboBoxTriggerLabel}
            comboLabel={comboBoxLabel}
            comboPlaceholder={comboBoxLabel}
            noResultsText={comboBoxNoResults}
            ComboBoxComponent={ComboBox}
          />
          <InlineToolbar
            {...props}
            pinButton={pinButton}
            defaultToolbar={getSavedToolbar()}
            onSetToolbar={onSetToolbar}
          />
        </>
      ),
      bottomToolbar: MetaToolbar,
      commandToolbar: (props) => (
        <CommandPalette
          {...props}
          noResultsText={gettext('No results')}
          ComboBoxComponent={ComboBox}
        />
      ),
      maxListNesting: 4,
      stripPastedStyles: false,
      ariaDescribedBy,
      ...newOptions,
      blockTypes: blockTypes.map(wrapWagtailIcon),
      inlineStyles: inlineStyles.map(wrapWagtailIcon),
      entityTypes,
      controls,
      decorators,
      plugins,
      commands,
      enableHorizontalRule,
    };
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
