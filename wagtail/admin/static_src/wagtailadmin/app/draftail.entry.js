import {
  initEditor,
  registry,
  ModalWorkflowSource,
  Link,
  Document,
  ImageBlock,
  EmbedBlock,
} from '../../../../../client/src/components/Draftail/index';

/**
 * Entry point loaded when the Draftail editor is in use.
 */
const draftail = registry;

// Expose Draftail as a global, with the initEditor function.
draftail.initEditor = initEditor;
window.draftail = draftail;

// Plugins for the built-in entities.
const plugins = [
  {
    type: 'DOCUMENT',
    source: ModalWorkflowSource,
    decorator: Document,
  },
  {
    type: 'LINK',
    source: ModalWorkflowSource,
    decorator: Link,
  },
  {
    type: 'IMAGE',
    source: ModalWorkflowSource,
    block: ImageBlock,
  },
  {
    type: 'EMBED',
    source: ModalWorkflowSource,
    block: EmbedBlock,
  },
];

plugins.forEach(draftail.registerPlugin);
