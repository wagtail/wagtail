import React from 'react';
import ReactDOM from 'react-dom';
import { Icon, Portal, initUpgradeNotification, initSkipLink } from '../..';
import { initModernDropdown, initTooltips } from '../../includes/initTooltips';
import { initTabs } from '../../includes/tabs';
import { dialog } from '../../includes/dialog';
import initCollapsibleBreadcrumbs from '../../includes/breadcrumbs';

if (process.env.NODE_ENV === 'development') {
  // Run react-axe in development only, so it does not affect performance
  // in production, and does not break unit tests either.
  // eslint-disable-next-line global-require, @typescript-eslint/no-var-requires, import/no-extraneous-dependencies
  const axe = require('react-axe');
  axe(React, ReactDOM, 1000);
}

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
  initSkipLink();
  dialog();
  initCollapsibleBreadcrumbs();
});
