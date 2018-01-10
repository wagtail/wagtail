import React from 'react';
import ReactDOM from 'react-dom';
import DraftailEditor from 'draftail';

import Icon from '../Icon/Icon';

import decorators from './decorators';
import sources from './sources';
import ImageBlock from './blocks/ImageBlock';
import EmbedBlock from './blocks/EmbedBlock';

import registry from './registry';

const wrapWagtailIcon = type => {
  if (type.icon) {
    return Object.assign(type, {
      icon: <Icon name={type.icon} />,
    });
  }

  return type;
}

export const initEditor = (fieldName, options = {}) => {
  const field = document.querySelector(`[name="${fieldName}"]`);
  const editorWrapper = document.createElement('div');
  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = rawContentState => {
    // TODO Remove default {} when finishing https://github.com/springload/wagtaildraftail/issues/32.
    field.value = JSON.stringify(rawContentState || {});
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
      }),
    );
  }

  const fieldValue = JSON.parse(field.value);
  // TODO Remove default null when finishing https://github.com/springload/wagtaildraftail/issues/32.
  const rawContentState =
    fieldValue && Object.keys(fieldValue).length === 0 ? null : fieldValue;

  const editor = (
    <DraftailEditor
      rawContentState={rawContentState}
      onSave={serialiseInputValue}
      placeholder="Write here…"
      {...options}
      blockTypes={blockTypes}
      inlineStyles={inlineStyles}
      entityTypes={entityTypes}
    />
  );

  ReactDOM.render(editor, editorWrapper);
};

// Register default Decorators and Sources
registry.registerDecorators(decorators);
registry.registerSources(sources);
registry.registerBlocks({
  ImageBlock,
  EmbedBlock,
});

const draftail = Object.assign(
  {
    initEditor: initEditor,
    // Expose basic React methods for basic needs
    // TODO Expose React as global as part of Wagtail vendor file instead of doing this.
    // createClass: React.createClass,
    // createElement: React.createElement,
  },
  registry,
);

export default draftail;
