import { Controller } from '@hotwired/stimulus';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Updates the server, using a PATCH request when the toggle is clicked on a dismissible
 * element initialized by DismissibleController
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
  data: Record<string, boolean | string>,
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
 * Initialize such elements with a default handler that performs the dismissal.
 * This only initializes elements that are rendered by the server (if they have the data attr), so elements
 * that are rendered by the client (e.g. React) needs to be handled separately.
 *
 * @example
 * ```html
 * <section
 *  data-controller="w-dismissible"
 *  data-w-dismissible-dismissed-class="w-dismissible--dismissed"
 *  data-w-dismissible-id-value="Whats new in Wagtail"
 * >
 *   <button type="button" data-action="w-dismiss#dismissible">Close</button>
 * </section>
 * ```
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
  toggle(event?: Event & { params?: { value?: boolean | string } }): void {
    this.element.classList.add(this.dismissedClass);
    this.dismissedValue = true;
    this.patch(event);
  }

  /**
   * Send a PATCH request to the server to update the dismissible state for the
   * given ID and update value.
   *
   * @param event - The event that triggered the patch, with optional params.
   * The param can technically be any value, but we currently only use booleans
   * and strings.
   */
  patch(event?: Event & { params?: { value?: boolean | string } }): void {
    if (!this.idValue) return;
    updateDismissibles({
      [this.idValue]: event?.params?.value ?? this.dismissedValue,
    });
  }
}
