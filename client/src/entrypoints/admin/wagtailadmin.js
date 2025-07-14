import initSidePanel from '../../includes/sidePanel';
import {
  initAnchoredPanels,
  initCollapsiblePanels,
} from '../../includes/panels';
import { initMinimap } from '../../components/Minimap';

/**
 * Add in here code to run once the page is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
  initSidePanel();
  initCollapsiblePanels();

  const editHandlerElement = document.querySelector('[data-edit-handler]');
  if (editHandlerElement) {
    const editHandlerJson =
      editHandlerElement.getAttribute('data-edit-handler');
    const packedEditHandler = JSON.parse(editHandlerJson);
    window.editHandler = window.telepath.unpack(packedEditHandler);
  }
});

/**
 * Prefer the document’s DOMContentLoaded if possible.
 * window `load` only fires once the page’s resources are loaded.
 */
window.addEventListener('load', () => {
  initAnchoredPanels();
  initMinimap();
});
