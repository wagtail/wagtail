import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Updates the server, using a PATCH request when the toggle is clicked on a dismissible
 * element initialised by initDismissibles
 *
 * @param data - The dismissible represented as an object with keys as
 * the id and its new state: whether it is dismissed (boolean)
 *
 * @return {Promise<Response>}
 *
 * @example
 * const data = { 'dismissible-1': true, 'dismissible-2': false };
 * const wagtailConfig = {}
 *
 * updateDismissibles(data, wagtailConfig);
 */
export function updateDismissibles(
  data: Record<string, boolean>,
): Promise<Response> {
  return fetch(WAGTAIL_CONFIG.ADMIN_URLS?.DISMISSIBLES, {
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
 * Initialise dismissibles fetched from server and add click event listeners to them.
 * @return {void}
 */
export function initDismissibles(): void {
  // A dismissible element is marked by the data-wagtail-dismissible-id attribute.
  const dismissibles = document.querySelectorAll<HTMLElement>(
    '[data-wagtail-dismissible-id]',
  );

  // Initialise such elements with a default handler that performs the dismissal.
  // This only initialises elements that are rendered by the server, so elements
  // that are rendered by the client (e.g. React) needs to be handled separately.
  dismissibles.forEach((dismissible: HTMLElement) => {
    // The toggle is marked by the data-wagtail-dismissible-toggle attribute,
    // which can either be the dismissible itself or a descendant element.
    const toggle = dismissible.hasAttribute('data-wagtail-dismissible-toggle')
      ? dismissible
      : dismissible.querySelector<HTMLElement>(
          '[data-wagtail-dismissible-toggle]',
        );
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
