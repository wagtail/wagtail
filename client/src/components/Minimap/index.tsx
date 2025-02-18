import React from 'react';
import ReactDOM from 'react-dom';
import { MinimapMenuItem } from './MinimapItem';

import { toggleCollapsiblePanel } from '../../includes/panels';
import { debounce } from '../../utils/debounce';

import Minimap from './Minimap';

/**
 * Generate a minimap link’s data, based on the panel’s elements.
 */
const createMinimapLink = (
  anchor: HTMLAnchorElement,
): MinimapMenuItem | null => {
  const panel = anchor.closest<HTMLElement>('[data-panel]');
  const headingId = panel?.getAttribute('aria-labelledby');
  const heading = panel?.querySelector<HTMLHeadingElement>(`#${headingId}`);
  const toggle = panel?.querySelector<HTMLButtonElement>('[data-panel-toggle]');
  // Special case for InlinePanel, where deleted items are kept until the form is saved.
  const inlinePanelDeleted = anchor.closest(
    '[data-inline-panel-child].deleted',
  );
  if (!panel || !heading || !toggle || inlinePanelDeleted) {
    return null;
  }

  const headingText = heading.querySelector('[data-panel-heading-text]');
  // If the heading’s most correct text content is unavailable (StreamField block collapsed when empty),
  // fall back to the full heading text.
  const label =
    headingText?.textContent ||
    heading.textContent?.replace(/\s+\*\s+$/g, '').trim();
  const required = panel.querySelector('[data-panel-required]') !== null;
  const useElt = toggle.querySelector<SVGUseElement>('use');
  const icon = useElt?.getAttribute('href')?.replace('#icon-', '') || '';
  const ariaLevel = heading.getAttribute('aria-level');
  const headingLevel = `h${ariaLevel || heading.tagName[1] || 2}`;
  const errorCount = [].slice
    .call(panel.querySelectorAll('.error-message'))
    .filter((err) => err.closest('[data-panel]') === panel).length;

  return {
    anchor,
    toggle,
    panel,
    icon,
    label: label || '',
    // Use the attribute rather than property so we only have a hash.
    href: anchor.getAttribute('href') || '',
    required,
    errorCount,
    level: headingLevel as MinimapMenuItem['level'],
  };
};

/**
 * Render the minimap component within a given element.
 * Populates the minimap with the relevant links based on currently-visible collapsible panels.
 */
const renderMinimap = (container: HTMLElement) => {
  let anchorsContainer: HTMLElement = document.body;
  const tabs = document.querySelector('[data-tabs]');

  // Render the minimap based on the active tab when there are tabs.
  if (tabs) {
    const activeTab = tabs.querySelector('[role="tab"][aria-selected="true"]');
    const panelId = activeTab?.getAttribute('aria-controls');
    const activeTabpanel = tabs.querySelector<HTMLElement>(`#${panelId}`);
    anchorsContainer = activeTabpanel || anchorsContainer;
  }

  const anchors = anchorsContainer.querySelectorAll<HTMLAnchorElement>(
    '[data-panel-anchor]',
  );
  const links: MinimapMenuItem[] = [].slice
    .call(anchors)
    .map(createMinimapLink)
    .filter(Boolean);

  const toggleAllPanels = (expanded) => {
    links.forEach((link, i) => {
      // Avoid collapsing the title field, where the collapse toggle is hidden.
      const isTitle = i === 0 && link.href.includes('title');
      if (!isTitle) {
        toggleCollapsiblePanel(link.toggle, expanded);
      }
    });
  };

  ReactDOM.render(
    <Minimap
      container={container}
      anchorsContainer={anchorsContainer}
      links={links}
      onUpdate={renderMinimap}
      toggleAllPanels={toggleAllPanels}
    />,
    container,
  );
};

/**
 * Initialize the minimap within the target element,
 * making sure it re-renders when the visible content changes.
 */
export const initMinimap = (
  container = document.querySelector<HTMLElement>('[data-minimap-container]'),
) => {
  if (!container) {
    return;
  }
  const anchors = document.body.querySelectorAll<HTMLAnchorElement>(
    '[data-panel-anchor]',
  );
  if (!anchors.length) {
    return;
  }

  const updateMinimap = debounce(renderMinimap.bind(null, container), 100);

  document.addEventListener('wagtail:tab-changed', updateMinimap);
  document.addEventListener('wagtail:panel-init', updateMinimap);

  // Make sure the positioning of the minimap is always correct.
  const setOffsetTop = () =>
    container.style.setProperty('--offset-top', `${container.offsetTop}px`);
  const updateOffsetTop = debounce(setOffsetTop, 100);

  window.addEventListener('resize', updateOffsetTop);

  setOffsetTop();
  updateMinimap(container);
};
