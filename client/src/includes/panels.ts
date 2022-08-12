/**
 * Switches a collapsible panel from expanded to collapsed, or vice versa.
 * Updates the DOM and fires custom events for other code to hook into.
 */
const toggleCollapsiblePanel = (
  toggle: HTMLButtonElement,
  content: HTMLElement,
  // If a specific state isn’t requested, read the DOM and toggle.
  expanded = !(toggle.getAttribute('aria-expanded') === 'true'),
) => {
  toggle.setAttribute('aria-expanded', `${expanded}`);

  if (expanded) {
    content.removeAttribute('hidden');
  } else if ('onbeforematch' in document.body) {
    // Use experimental `until-found` value, so users can search inside the panels.
    content.setAttribute('hidden', 'until-found');
  } else {
    // Browsers without support for `until-found` will not have this value set
    content.setAttribute('hidden', '');
  }

  content.dispatchEvent(
    new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
  );
  content.dispatchEvent(
    new CustomEvent('wagtail:panel-toggle', {
      bubbles: true,
      cancelable: false,
      detail: { expanded },
    }),
  );
};

/**
 * Initialises event handlers for a collapsible panel,
 * and applies the correct initial state based on classes.
 */
function initCollapsiblePanel(toggle: HTMLButtonElement) {
  const panel = toggle.closest<HTMLElement>('[data-panel]');
  const content = document.querySelector<HTMLDivElement>(
    `#${toggle.getAttribute('aria-controls')}`,
  );

  if (!content || !panel) {
    return;
  }

  const togglePanel = toggleCollapsiblePanel.bind(null, toggle, content);

  // Collapse panels marked as `collapsed`, unless they contain invalid fields.
  const hasCollapsed = panel.classList.contains('collapsed');
  const hasError = content.querySelector(
    '[aria-invalid="true"], .error, .w-field--error',
  );

  if (hasCollapsed && !hasError) {
    togglePanel(false);
  }

  toggle.addEventListener('click', togglePanel.bind(null, undefined));

  const heading = panel.querySelector<HTMLElement>('[data-panel-heading]');
  if (heading) {
    heading.addEventListener('click', togglePanel.bind(null, undefined));
  }

  // Set the toggle back to expanded upon reveal.
  content.addEventListener('beforematch', togglePanel.bind(null, true));
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
 * JS-rendered :target.
 */
export function initAnchoredPanels(
  anchorTarget = document.querySelector<HTMLElement>('[data-panel]:target'),
) {
  if (anchorTarget) {
    anchorTarget.scrollIntoView({ behavior: 'smooth' });
  }
}
