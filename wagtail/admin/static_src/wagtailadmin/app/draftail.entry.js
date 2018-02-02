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
 * Expose as a global, and register the built-in entities.
 */

window.draftail = registry;
window.draftail.initEditor = initEditor;

window.draftail.registerSources({
  ModalWorkflowSource,
});

window.draftail.registerDecorators({
  Link,
  Document,
});

window.draftail.registerBlocks({
  ImageBlock,
  EmbedBlock,
});
