import React from 'react';
import ReactDOM from 'react-dom';
import {
  Icon,
  Portal,
  initDismissibles,
  initSkipLink,
  initUpgradeNotification,
} from '../..';
import { initModernDropdown, initTooltips } from '../../includes/initTooltips';
import { initTabs } from '../../includes/tabs';
import { dialog } from '../../includes/dialog';
import initCollapsibleBreadcrumbs from '../../includes/breadcrumbs';
import initSidePanel from '../../includes/sidePanel';
import {
  initAnchoredPanels,
  initCollapsiblePanels,
} from '../../includes/panels';
import { initMinimap } from '../../components/Minimap';

// Expose components as globals for third-party reuse.
window.wagtail.components = {
  Icon,
  Portal,
};

/**
 * Add in here code to run once the page is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
  initUpgradeNotification();
  initTooltips();
  initModernDropdown();
  initTabs();
  initDismissibles();
  initSkipLink();
  dialog();
  initCollapsibleBreadcrumbs();
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
