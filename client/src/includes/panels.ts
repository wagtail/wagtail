import { getElementByContentPath } from '../utils/contentPath';

const PANEL_EXPANDED_STORAGE_KEY = 'wagtail:panel-expanded';
type PanelStates = Record<string, Record<string, boolean>>;

const getPanelStates = (): PanelStates => {
  try {
    return (
      JSON.parse(localStorage.getItem(PANEL_EXPANDED_STORAGE_KEY) || '{}') ?? {}
    );
  } catch {
    // Use the default state if browser storage is unavailable or invalid.
    return {};
  }
};

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
 * Initializes event handlers and restores saved state,
 * falling back to the panel's classes.
 */
export function initCollapsiblePanel(toggle: HTMLButtonElement) {
  const panel = toggle.closest<HTMLElement>('[data-panel]');
  const content = document.querySelector<HTMLDivElement>(
    `#${toggle.getAttribute('aria-controls')}`,
  );

  // Avoid initializing the same panel twice.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  if (!content || !panel || panel.collapsibleInitialised) {
    return;
  }

  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  panel.collapsibleInitialised = true;

  const togglePanel = toggleCollapsiblePanel.bind(null, toggle);

  // Saved state overrides the default, but must not hide validation errors.
  const savedExpanded =
    getPanelStates()[window.location.pathname]?.[content.id];
  const hasCollapsed =
    typeof savedExpanded === 'boolean'
      ? !savedExpanded
      : panel.classList.contains('collapsed');
  const hasError = content.querySelector(
    '[aria-invalid="true"], .error, .w-field--error',
  );
  const isCollapsed = hasCollapsed && !hasError;

  if (isCollapsed) {
    togglePanel(false);
  }

  // Listen after restoring state so initialization does not overwrite preferences.
  toggle.addEventListener('wagtail:panel-toggle', () => {
    const states = getPanelStates();
    const { pathname } = window.location;
    try {
      localStorage.setItem(
        PANEL_EXPANDED_STORAGE_KEY,
        JSON.stringify({
          ...states,
          [pathname]: {
            ...states[pathname],
            [content.id]: toggle.getAttribute('aria-expanded') === 'true',
          },
        }),
      );
    } catch {
      // Panels remain usable if browser storage is unavailable or full.
    }
  });

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
 * Make panels collapsible, restoring saved state or the `collapsed` default.
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
  anchorTarget = window.location.hash
    ? document.getElementById(window.location.hash.slice(1))
    : null,
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
