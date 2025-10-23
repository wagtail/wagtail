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

import { setAttrs } from '../../utils/attrs';
import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';
import { InputNotFoundError } from '../Widget/index';

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
import { DraftailInsertBlockCommand } from './commands/InsertBlock';
import { DraftailSplitCommand } from './commands/Split';

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
 * Initializes the DraftailEditor for a given field.
 * @param {string} selector
 * @param {object} originalOptions
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

    // Only initialize the character count / max length on fields explicitly requiring it.
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

class BoundDraftailWidget {
  constructor(input, options, parentCapabilities, shouldInitEditor) {
    this.input = input;
    this.capabilities = new Map(parentCapabilities);
    this.options = options;

    if (shouldInitEditor) {
      const [, setOptions] = initEditor(
        '#' + this.input.id,
        this.getFullOptions(),
        document.currentScript,
      );
      this.setDraftailOptions = setOptions;
    } else {
      this.setDraftailOptions = null;
    }
  }

  getValue() {
    return this.input.value;
  }

  getState() {
    return this.input.draftailEditor.getEditorState();
  }

  setState(editorState) {
    this.input.draftailEditor.onChange(editorState);
  }

  setInvalid(invalid) {
    if (invalid) {
      this.input.setAttribute('aria-invalid', 'true');
    } else {
      this.input.removeAttribute('aria-invalid');
    }
  }

  getTextLabel(opts) {
    const maxLength = opts && opts.maxLength;
    if (!this.input.value) return '';
    const value = JSON.parse(this.input.value);
    if (!value || !value.blocks) return '';

    let result = '';
    for (const block of value.blocks) {
      if (block.text) {
        result += result ? ' ' + block.text : block.text;
        if (maxLength && result.length > maxLength) {
          return result.substring(0, maxLength - 1) + '…';
        }
      }
    }
    return result;
  }

  focus() {
    setTimeout(() => {
      this.input.draftailEditor.focus();
    }, 50);
  }

  setCapabilityOptions(capability, capabilityOptions) {
    if (!this.setDraftailOptions) {
      throw new Error(
        'setCapabilityOptions is only supported on Draftail widgets rendered via DraftailRichTextArea.render',
      );
    }
    const newCapability = Object.assign(
      this.capabilities.get(capability),
      capabilityOptions,
    );
    this.capabilities.set(capability, newCapability);
    this.setDraftailOptions(this.getFullOptions());
  }

  /**
   * Given a mapping of the capabilities supported by this widget's container,
   * return the options overrides that enable additional widget functionality
   * (e.g. splitting or adding additional blocks).
   * Non-context-dependent Draftail options are available here as this.options.
   */
  getCapabilityOptions(parentCapabilities) {
    const options = {};
    const capabilities = parentCapabilities;
    const split = capabilities.get('split');
    const addSibling = capabilities.get('addSibling');
    let blockCommands = [];
    if (split) {
      const blockGroups =
        addSibling && addSibling.enabled && split.enabled
          ? addSibling.blockGroups
          : [];
      // Create commands for splitting + inserting a block. This requires both the split
      // and addSibling capabilities to be available and enabled
      blockCommands = blockGroups.map(([group, blocks]) => {
        const blockControls = blocks.map(
          (blockDef) =>
            new DraftailInsertBlockCommand(this, blockDef, addSibling, split),
        );
        return {
          label: group || gettext('Blocks'),
          type: `streamfield-${group}`,
          items: blockControls,
        };
      });

      if (split.enabled) {
        blockCommands.push({
          label: gettext('Actions'),
          type: 'custom-actions',
          items: [new DraftailSplitCommand(this, split)],
        });
      }
    }

    options.commands = [
      {
        type: 'blockTypes',
      },
      {
        type: 'entityTypes',
      },
      ...blockCommands,
    ];

    return options;
  }

  getFullOptions() {
    return {
      ...this.options,
      ...this.getCapabilityOptions(this.capabilities),
    };
  }
}

class DraftailRichTextArea {
  constructor(options) {
    this.options = options;
  }

  render(container, name, id, initialState, parentCapabilities, options = {}) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.id = id;
    input.name = name;

    if (typeof options?.attributes === 'object') {
      setAttrs(input, options.attributes);
    }
    // If the initialState is an EditorState, rather than serialized rawContentState, it's
    // easier for us to initialize the widget blank and then setState to the correct state
    const initialiseBlank = !!initialState.getCurrentContent;
    input.value = initialiseBlank ? 'null' : initialState;
    container.appendChild(input);

    const boundDraftail = new BoundDraftailWidget(
      input,
      { ...this.options, ...options },
      parentCapabilities,
      true, // shouldInitEditor
    );

    if (initialiseBlank) {
      boundDraftail.setState(initialState);
    }

    return boundDraftail;
  }

  getByName(name, container) {
    const selector = `input[name="${name}"]`;
    let input;
    if (container.matches(selector)) {
      input = container;
    } else {
      input = container.querySelector(selector);
    }
    if (!input) {
      throw new InputNotFoundError(name);
    }

    return new BoundDraftailWidget(input, this.options, null, false);
  }
}

export default {
  initEditor,
  splitState,
  registerPlugin,
  DraftUtils,
  DraftailRichTextArea,
  // Components exposed for third-party reuse.
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
  Tooltip,
  TooltipEntity,
};
