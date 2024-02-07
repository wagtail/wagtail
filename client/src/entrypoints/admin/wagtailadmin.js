import { initTabs } from '../../includes/tabs';
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
  initTabs();
  initSidePanel();
  initCollapsiblePanels();
});

/**
 * Prefer the document’s DOMContentLoaded if possible.
 * window `load` only fires once the page’s resources are loaded.
 */
window.addEventListener('load', () => {
  initAnchoredPanels();
  initMinimap();
});
