import * as Draftail from 'draftail';
import draftail, {
  Link,
  Document,
  ImageBlock,
  EmbedBlock,
} from '../../../../../client/src/components/Draftail/index';

/**
 * Entry point loaded when the Draftail editor is in use.
 */

 // Expose Draftail package as a global.
window.Draftail = Draftail;
// Expose module as a global.
window.draftail = draftail;

// Plugins for the built-in entities.
const plugins = [
  {
    type: 'DOCUMENT',
    source: draftail.ModalWorkflowSource,
    decorator: Document,
  },
  {
    type: 'LINK',
    source: draftail.ModalWorkflowSource,
    decorator: Link,
  },
  {
    type: 'IMAGE',
    source: draftail.ModalWorkflowSource,
    block: ImageBlock,
  },
  {
    type: 'EMBED',
    source: draftail.ModalWorkflowSource,
    block: EmbedBlock,
  },
];

plugins.forEach(draftail.registerPlugin);
