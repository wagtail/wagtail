import React from 'react';
import ReactDOM from 'react-dom';
import DraftailEditor from 'draftail';

import Icon from '../Icon/Icon';

import decorators from './decorators';
import sources from './sources';
import registry from './registry';

export const initEditor = (fieldName, options = {}) => {
  const field = document.querySelector(`[name="${fieldName}"]`);
  const editorWrapper = document.createElement('div');
  field.parentNode.appendChild(editorWrapper);

  const serialiseInputValue = (rawContentState) => {
    // TODO Remove default {} when finishing https://github.com/springload/wagtaildraftail/issues/32.
    field.value = JSON.stringify(rawContentState || {});
  };

  let blockTypes;
  let inlineStyles;
  let entityTypes;

  if (options && options.blockTypes) {
    blockTypes = options.blockTypes.map(type => Object.assign(type, {
      icon: <Icon name={type.icon} />,
    }));
  }

  if (options && options.inlineStyles) {
    inlineStyles = options.inlineStyles.map(type => Object.assign(type, {
      icon: <Icon name={type.icon} />,
    }));
  }

  if (options && options.entityTypes) {
    entityTypes = options.entityTypes.map(type => Object.assign(type, {
      icon: <Icon name={type.icon} />,
      source: registry.getSource(type.source),
      strategy: registry.getStrategy(type.type) || null,
      decorator: registry.getDecorator(type.decorator),
    }));
  }

  const fieldValue = JSON.parse(field.value);
  // TODO Remove default null when finishing https://github.com/springload/wagtaildraftail/issues/32.
  const rawContentState = fieldValue && Object.keys(fieldValue).length === 0 ? null : fieldValue;

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

const draftail = Object.assign({
  initEditor: initEditor,
  // Expose basic React methods for basic needs
  // TODO Expose React as global as part of Wagtail vendor file instead of doing this.
  // createClass: React.createClass,
  // createElement: React.createElement,
}, registry);

export default draftail;
