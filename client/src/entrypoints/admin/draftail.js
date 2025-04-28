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

// This file is included and run when there's a DraftailRichTextArea widget in the response.
// Normally this is only included once in the initial page load, but it may be included
// more than once when there's an AJAX response that includes the widget, e.g. in choosers.
// Ensure we only run the initialization code once.
// https://github.com/wagtail/wagtail/issues/12002
if (!window.Draftail || !window.draftail) {
  // Expose Draftail package as a global.
  window.Draftail = Draftail;
  // Expose module as a global.
  window.draftail = draftail;

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

  /**
   * Initialize a Draftail editor on a given element when the w-draftail:init event is fired.
   */
  document.addEventListener('w-draftail:init', ({ detail = {}, target }) => {
    const id = target.id;

    if (!id) {
      // eslint-disable-next-line no-console
      console.error('`w-draftail:init` event must have a target with an id.');
      return;
    }

    window.draftail.initEditor(`#${id}`, detail, document.currentScript);
  });
}
