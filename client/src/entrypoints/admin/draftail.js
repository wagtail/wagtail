import * as Draftail from 'draftail';
import draftail, {
  Link,
  onPasteLink,
  Document,
  ImageBlock,
  EmbedBlock,
} from '../../components/Draftail/index';

/**
 * Entry point loaded when the Draftail editor is in use.
 */

// Expose Draftail package as a global.
window.Draftail = Draftail;
// Expose module as a global.
window.draftail = draftail;

/** @deprecated RemovedInWagtail70 - Ensure that any third party packages that use global.chooserUrls can still append to this global object until support is removed. */
window.chooserUrls = global.chooserUrls || {};

// Plugins for the built-in entities.
const entityTypes = [
  {
    type: 'DOCUMENT',
    source: draftail.DocumentModalWorkflowSource,
    decorator: Document,
  },
  {
    type: 'LINK',
    source: draftail.LinkModalWorkflowSource,
    decorator: Link,
    onPaste: onPasteLink,
  },
  {
    type: 'IMAGE',
    source: draftail.ImageModalWorkflowSource,
    block: ImageBlock,
  },
  {
    type: 'EMBED',
    source: draftail.EmbedModalWorkflowSource,
    block: EmbedBlock,
  },
];

entityTypes.forEach((type) => draftail.registerPlugin(type, 'entityTypes'));
