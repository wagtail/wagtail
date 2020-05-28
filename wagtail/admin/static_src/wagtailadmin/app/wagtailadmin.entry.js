import React from 'react';
import ReactDOM from 'react-dom';
import {
  Icon,
  Portal,
  initExplorer,
  initFocusOutline,
  initSubmenus,
  initSkipLink,
  initIE11Warning,
  initUpgradeNotification,
} from '../../../../../client/src/index';

if (process.env.NODE_ENV === 'development') {
  // Run react-axe in development only, so it does not affect performance
  // in production, and does not break unit tests either.
  // eslint-disable-next-line global-require
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
  const explorerNode = document.querySelector('[data-explorer-menu]');
  const toggleNode = document.querySelector('[data-explorer-start-page]');

  if (explorerNode && toggleNode) {
    initExplorer(explorerNode, toggleNode);
  }

  initFocusOutline();
  initSubmenus();
  initIE11Warning();
  initUpgradeNotification();
  initSkipLink();
});
