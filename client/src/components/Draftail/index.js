import React from 'react';
import ReactDOM from 'react-dom';
import { DraftailEditor } from 'draftail';

import { IS_IE11, STRINGS } from '../../config/wagtailConfig';

import Icon from '../Icon/Icon';

import Link from './decorators/Link';
import Document from './decorators/Document';
import ImageBlock from './blocks/ImageBlock';
import EmbedBlock from './blocks/EmbedBlock';

import ModalWorkflowSource from './sources/ModalWorkflowSource';

import registry from './registry';

const wrapWagtailIcon = type => {
  const isIconFont = type.icon && typeof type.icon === 'string';
  if (isIconFont) {
    return Object.assign(type, {
      icon: <Icon name={type.icon} />,
    });
  }

  return type;
};

export const initEditor = (fieldName, options = {}) => {
  const field = document.querySelector(`[name="${fieldName}"]`);
  const editorWrapper = document.createElement('div');
  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = rawContentState => {
    field.value = JSON.stringify(rawContentState);
  };

  let blockTypes;
  let inlineStyles;
  let entityTypes;

  if (options && options.blockTypes) {
    blockTypes = options.blockTypes.map(wrapWagtailIcon);
  }

  if (options && options.inlineStyles) {
    inlineStyles = options.inlineStyles.map(wrapWagtailIcon);
  }

  if (options && options.entityTypes) {
    entityTypes = options.entityTypes.map(wrapWagtailIcon).map(type =>
      Object.assign(type, {
        source: registry.getSource(type.source),
        strategy: registry.getStrategy(type.type) || null,
        decorator: registry.getDecorator(type.decorator),
        block: registry.getBlock(type.block),
      })
    );
  }

  const enableHorizontalRule = options && options.enableHorizontalRule ? {
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
      blockTypes={blockTypes}
      inlineStyles={inlineStyles}
      entityTypes={entityTypes}
      enableHorizontalRule={enableHorizontalRule}
    />
  );

  const draftailEditor = ReactDOM.render(editor, editorWrapper);

  // Bind editor instance to its field so it can be accessed imperatively elsewhere.
  field.draftailEditor = draftailEditor;
};

registry.registerSources({
  ModalWorkflowSource,
});
registry.registerDecorators({
  Link,
  Document,
});
registry.registerBlocks({
  ImageBlock,
  EmbedBlock,
});

const draftail = Object.assign(
  {
    initEditor,
  },
  registry
);

export default draftail;
