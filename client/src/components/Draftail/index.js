import React from 'react';
import ReactDOM from 'react-dom';
import { DraftailEditor } from 'draftail';

import { IS_IE11, STRINGS } from '../../config/wagtailConfig';

import Icon from '../Icon/Icon';

import registry from './registry';

export { registry };

export { default as Link } from './decorators/Link';
export { default as Document } from './decorators/Document';
export { default as ImageBlock } from './blocks/ImageBlock';
export { default as EmbedBlock } from './blocks/EmbedBlock';

export { default as ModalWorkflowSource } from './sources/ModalWorkflowSource';

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
 * @param {string} fieldName
 * @param {Object} options
 */
export const initEditor = (fieldName, options) => {
  const field = document.querySelector(`[name="${fieldName}"]`);
  const editorWrapper = document.createElement('div');
  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = rawContentState => {
    field.value = JSON.stringify(rawContentState);
  };

  const blockTypes = options.blockTypes || [];
  const inlineStyles = options.inlineStyles || [];
  let entityTypes = options.entityTypes || [];

  entityTypes = entityTypes.map(wrapWagtailIcon).map((type) => {
    const plugin = registry.getPlugin(type.type);
    // Override the properties defined in the JS plugin: Python should be the source of truth.

    return Object.assign({}, plugin, type);
  });

  const enableHorizontalRule = options.enableHorizontalRule ? {
    description: STRINGS.HORIZONTAL_LINE,
  } : false;

  const rawContentState = JSON.parse(field.value);

  const editor = (
    <DraftailEditor
      rawContentState={rawContentState}
      onSave={serialiseInputValue}
      placeholder={STRINGS.WRITE_HERE}
      spellCheck={true}
      enableLineBreak={{ description: STRINGS.LINE_BREAK }}
      showUndoControl={{ description: STRINGS.UNDO }}
      showRedoControl={{ description: STRINGS.REDO }}
      // If increasing above 4, we will need to add styles for the extra nesting levels.
      maxListNesting={4}
      // Draft.js + IE 11 presents some issues with pasting rich text. Disable rich paste there.
      stripPastedStyles={IS_IE11}
      {...options}
      blockTypes={blockTypes.map(wrapWagtailIcon)}
      inlineStyles={inlineStyles.map(wrapWagtailIcon)}
      entityTypes={entityTypes}
      enableHorizontalRule={enableHorizontalRule}
    />
  );

  const draftailEditor = ReactDOM.render(editor, editorWrapper);

  // Bind editor instance to its field so it can be accessed imperatively elsewhere.
  field.draftailEditor = draftailEditor;
};
