import { initExplorer } from 'wagtail-client';

/**
 * Admin JS entry point. Add in here code to run once the page is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
  const explorerNode = document.querySelector('[data-explorer-menu]');
  const toggleNode = document.querySelector('[data-explorer-start-page]');

  if (explorerNode && toggleNode) {
    initExplorer(explorerNode, toggleNode);
  }
});
