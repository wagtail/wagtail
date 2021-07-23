import { initExplorer } from '../../components/Explorer';
import { initSubmenus } from '../../includes/initSubmenus';
import { initSkipLink } from '../../includes/initSkipLink';

document.addEventListener('DOMContentLoaded', () => {
  const explorerNode = document.querySelector('[data-explorer-menu]');
  const toggleNode = document.querySelector('[data-explorer-start-page]');

  if (explorerNode && toggleNode) {
    initExplorer(explorerNode, toggleNode);
  }

  initSubmenus();
  initSkipLink();
});
