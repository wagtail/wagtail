import React from 'react';
import ReactDOM from 'react-dom';
import DraftailEditor from 'draftail';

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

  if (options.entityTypes) {
    // eslint-disable-next-line no-param-reassign
    options.entityTypes = options.entityTypes.map(entity => Object.assign(entity, {
      source: registry.getSource(entity.source),
      strategy: registry.getStrategy(entity.type) || null,
      decorator: registry.getDecorator(entity.decorator),
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
