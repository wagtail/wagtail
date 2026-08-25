import { initMinimap } from '../../components/Minimap';
import {
  initAnchoredPanels,
  initCollapsiblePanels,
} from '../../includes/panels';
import initSidePanel from '../../includes/sidePanel';

/**
 * Add in here code to run once the page is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
  initSidePanel();
  initCollapsiblePanels();

  const editHandlerElement = document.getElementById('w-edit-handler-data');
  if (editHandlerElement) {
    const packedEditHandler = JSON.parse(editHandlerElement.textContent);
    window.wagtail.editHandler = window.telepath.unpack(packedEditHandler);
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
