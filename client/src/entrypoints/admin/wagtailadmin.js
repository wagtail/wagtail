import { initTooltips } from '../../includes/initTooltips';
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
  initTooltips();
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

/**
 * When search results are successful, reinitialise widgets
 * that could be inside the newly injected DOM.
 */
window.addEventListener('w-swap:success', () => {
  initTooltips(); // reinitialise any tooltips
});
