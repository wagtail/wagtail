import { Controller } from '@hotwired/stimulus';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Updates the server, using a PATCH request when the toggle is clicked on a dismissible
 * element initialised by DismissibleController
 *
 * @param data - The dismissible represented as an object with keys as
 * the id and its new state: whether it is dismissed (boolean)
 *
 * @example
 * const data = { 'dismissible-1': true, 'dismissible-2': false };
 * const wagtailConfig = {}
 *
 * updateDismissibles(data, wagtailConfig);
 */
export const updateDismissibles = (
  data: Record<string, boolean>,
): Promise<Response> =>
  fetch(WAGTAIL_CONFIG.ADMIN_URLS?.DISMISSIBLES, {
    method: 'PATCH',
    headers: {
      [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    mode: 'same-origin',
  });

/**
 * Adds the ability to make an element dismissible so that it updates it's class and makes an async request.
 * Initialise such elements with a default handler that performs the dismissal.
 * This only initialises elements that are rendered by the server (if they have the data attr), so elements
 * that are rendered by the client (e.g. React) needs to be handled separately.
 *
 * @example
 * <section
 *  data-controller="w-dismissible"
 *  data-w-dismissible-dismissed-class="w-dismissible--dismissed"
 *  data-w-dismissible-id-value="Whats new in Wagtail"
 * >
 *  <button type="button" data-action="w-dismiss#dismissible">Close</button>
 * </section>
 */
export class DismissibleController extends Controller<HTMLElement> {
  static classes = ['dismissed'];

  static values = {
    dismissed: { default: false, type: Boolean },
    id: { default: '', type: String },
  };

  declare dismissedValue: boolean;
  declare idValue: string;
  declare readonly dismissedClass: string;

  /**
   * Upon activating the toggle, send an update to the server and add the
   * appropriate class and data attribute optimistically. Each dismissible
   * defines how it uses (or not) these indicators.
   */
  toggle(): void {
    if (!this.idValue) return;
    this.element.classList.add(this.dismissedClass);
    this.dismissedValue = true;
    updateDismissibles({ [this.idValue]: true });
  }
}
