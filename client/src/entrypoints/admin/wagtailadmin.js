import React from 'react';
import ReactDOM from 'react-dom';
import {
  Icon,
  Portal,
  initFocusOutline,
  initIE11Warning,
  initUpgradeNotification,
} from '../..';

if (process.env.NODE_ENV === 'development') {
  // Run react-axe in development only, so it does not affect performance
  // in production, and does not break unit tests either.
  // eslint-disable-next-line global-require, @typescript-eslint/no-var-requires
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
  initFocusOutline();
  initIE11Warning();
  initUpgradeNotification();
});
