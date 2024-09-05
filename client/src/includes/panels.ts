import { getElementByContentPath } from '../utils/contentPath';

/**
 * Switches a collapsible panel from expanded to collapsed, or vice versa.
 * Updates the DOM and fires custom events for other code to hook into.
 */
export const toggleCollapsiblePanel = (
  toggle: HTMLButtonElement,
  // If a specific state isn’t requested, read the DOM and toggle.
  isExpanding = !(toggle.getAttribute('aria-expanded') === 'true'),
) => {
  const content = document.querySelector<HTMLDivElement>(
    `#${toggle.getAttribute('aria-controls')}`,
  );

  if (!content) {
    return;
  }

  toggle.setAttribute('aria-expanded', `${isExpanding}`);

  if (isExpanding) {
    content.removeAttribute('hidden');
  } else if ('onbeforematch' in document.body) {
    // Use experimental `until-found` value, so users can search inside the panels.
    content.setAttribute('hidden', 'until-found');
  } else {
    // Browsers without support for `until-found` will not have this value set
    content.setAttribute('hidden', '');
  }

  // Fire events on the toggle so we can retrieve the content with aria-controls.
  toggle.dispatchEvent(
    new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
  );
  toggle.dispatchEvent(
    new CustomEvent('wagtail:panel-toggle', {
      bubbles: true,
      cancelable: false,
      detail: { expanded: isExpanding },
    }),
  );
};

/**
 * Initialises event handlers for a collapsible panel,
 * and applies the correct initial state based on classes.
 */
export function initCollapsiblePanel(toggle: HTMLButtonElement) {
  const panel = toggle.closest<HTMLElement>('[data-panel]');
  const content = document.querySelector<HTMLDivElement>(
    `#${toggle.getAttribute('aria-controls')}`,
  );

  // Avoid initialising the same panel twice.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  if (!content || !panel || panel.collapsibleInitialised) {
    return;
  }

  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  panel.collapsibleInitialised = true;

  const togglePanel = toggleCollapsiblePanel.bind(null, toggle);

  // Collapse panels marked as `collapsed`, unless they contain invalid fields.
  const hasCollapsed = panel.classList.contains('collapsed');
  const hasError = content.querySelector(
    '[aria-invalid="true"], .error, .w-field--error',
  );
  const isCollapsed = hasCollapsed && !hasError;

  if (isCollapsed) {
    togglePanel(false);
  }

  toggle.addEventListener('click', togglePanel.bind(null, undefined));

  const heading = panel.querySelector<HTMLElement>('[data-panel-heading]');
  if (heading) {
    heading.addEventListener('click', togglePanel.bind(null, undefined));
  }

  // Set the toggle back to expanded upon reveal.
  content.addEventListener('beforematch', togglePanel.bind(null, true));

  toggle.dispatchEvent(
    new CustomEvent('wagtail:panel-init', {
      bubbles: true,
      cancelable: false,
      detail: { expanded: !isCollapsed },
    }),
  );
}

/**
 * Make panels collapsible, and collapse panels already marked as `collapsed`.
 */
export function initCollapsiblePanels(
  toggles = document.querySelectorAll<HTMLButtonElement>('[data-panel-toggle]'),
) {
  toggles.forEach(initCollapsiblePanel);
}

/**
 * Smooth scroll onto any active panel.
 * Needs to run after the whole page is loaded so the browser can resolve any
 * JS-rendered elements.
 */
export function initAnchoredPanels(
  anchorTarget = document.getElementById(window.location.hash.slice(1)),
) {
  const target = anchorTarget?.matches('[data-panel]')
    ? anchorTarget
    : getElementByContentPath();

  if (target) {
    setTimeout(() => {
      target.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }
}
