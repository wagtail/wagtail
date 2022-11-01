
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Sends a PATCH request and updates the dismissibles field
 * of a UserProfile model.
 * @param data 
 * @returns 
 * Ensures the state "What's New in Wagtail" remains dismissed after being dismissed in the UserProfile
 */
export function updateDismissibles(data: Record<string, boolean>) {
  return fetch(WAGTAIL_CONFIG.ADMIN_URLS.DISMISSIBLES, {
    method: 'PATCH',
    headers: {
      [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    mode: 'same-origin',
  });
}

/**
 * Initializes server rendered elements.
 * Dismissible elements triggered on toggle click, which updates the server to dismiss the state "What's New in Wagtail"
 */
export function initDismissibles() {
  // A dismissible element is marked by the data-wagtail-dismissible-id attribute.
  const dismissibles = document.querySelectorAll<HTMLElement>(
    '[data-wagtail-dismissible-id]',
  );

  // Initialise such elements with a default handler that performs the dismissal.
  // This only initialises elements that are rendered by the server, so elements
  // that are rendered by the client (e.g. React) needs to be handled separately.
  dismissibles.forEach((dismissible) => {
    // The toggle is marked by the data-wagtail-dismissible-toggle attribute,
    // which can either be the dismissible itself or a descendant element.
    const toggle = dismissible.hasAttribute('data-wagtail-dismissible-toggle')
      ? dismissible
      : dismissible.querySelector('[data-wagtail-dismissible-toggle]');

    const id = dismissible.dataset.wagtailDismissibleId;
    if (!(toggle && id)) return;

    // Upon clicking the toggle, send an update to the server and add the
    // appropriate class and data attribute optimistically. Each dismissible
    // defines how it uses (or not) these indicators.
    toggle.addEventListener('click', () => {
      updateDismissibles({ [id]: true });
      dismissible.classList.add('w-dismissible--dismissed');
      dismissible.setAttribute('data-wagtail-dismissed', '');
    });
  });
}
