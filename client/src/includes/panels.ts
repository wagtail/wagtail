/**
 * Switches a collapsible panel from expanded to collapsed, or vice versa.
 * Updates the DOM and fires custom events for other code to hook into.
 */
const toggleCollapsiblePanel = (
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

  content.dispatchEvent(
    new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
  );
  content.dispatchEvent(
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
function initCollapsiblePanel(toggle: HTMLButtonElement) {
  const panel = toggle.closest<HTMLElement>('[data-panel]');
  const content = document.querySelector<HTMLDivElement>(
    `#${toggle.getAttribute('aria-controls')}`,
  );

  if (!content || !panel) {
    return;
  }

  const togglePanel = toggleCollapsiblePanel.bind(null, toggle);

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
 * Initialises event handlers for collapsing / expanding all panels
 */
export function initCollapseAllPanels(
  button = document.querySelector<HTMLButtonElement>(
    '[data-all-panels-toggle]',
  ),
) {
  if (!button) {
    return;
  }

  const expandText = button.getAttribute('data-expand-text');
  const collapseText = button.getAttribute('data-collapse-text');

  if (!button || !expandText || !collapseText) {
    return;
  }

  button.addEventListener('click', () => {
    const isExpanding = !(button.getAttribute('aria-expanded') === 'true');

    // Find all panel toggles within the same form as the button,
    // excluding the special "title" panel that has no toggle.
    const toggles = button
      .closest('form')
      ?.querySelectorAll<HTMLButtonElement>(
        '[data-panel]:not(.title) [data-panel-toggle]',
      );

    if (!toggles) {
      return;
    }

    button.setAttribute('aria-expanded', `${isExpanding}`);

    toggles.forEach((toggle: HTMLButtonElement) => {
      toggleCollapsiblePanel(toggle, isExpanding);
    });

    // eslint-disable-next-line no-param-reassign
    button.innerText = isExpanding ? collapseText : expandText;
  });
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
