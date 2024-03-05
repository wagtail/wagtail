import { Controller } from '@hotwired/stimulus';

/**
 * Adds the ability for the controlled element to reflect the query parameters
 * of an event's URL or the current URL in window.location to its own URL. This
 * allows the element's URL to be dynamically updated in response to a
 * client-side update e.g. listings refresh.
 *
 * @example - Reflecting the query parameters from the current URL
 * ```html
 * <a
 *   href="add/"
 *   data-controller="w-link"
 *   data-w-link-reflect-keys-value='["collection_id"]'
 *   data-action="w-swap:reflect@document->w-link#setParams"
 * >
 *   Add
 * </a>
 * ```
 *
 * If the `window.location` URL contains a query parameter `collection_id` at
 * the time the controller is connected (or when there is `w-swap:reflect`
 * event), the new URL's parameters (that are specified in reflect-keys-value)
 * will be reflected to the `href` attribute of the element, e.g.
 * `"add/?collection_id=1"`.
 */
export class LinkController extends Controller<HTMLElement> {
  static values = {
    attrName: { default: 'href', type: String },
    preserveKeys: { default: [], type: Array },
    reflectKeys: { default: [], type: Array },
  };

  /** Attribute on the controlled element containing the URL string. */
  declare attrNameValue: string;
  /** URL param keys in the element's URL that will never be updated. */
  declare preserveKeysValue: string[];
  /**
   * URL param keys to be updated in the element's URL from the source URL.
   * If unset before the controller is connected, this will be set to the keys
   * in the current URL's parameters.
   */
  declare reflectKeysValue: string[];

  get url() {
    return new URL(
      this.element.getAttribute(this.attrNameValue) || '',
      window.location.href,
    );
  }

  connect() {
    this.setParams();
  }

  reflectKeysValueChanged(_: string[], oldValue?: string[]) {
    // If reflectKeys is unset before the controller is connected,
    // we'll be reflecting all keys that are present in the URL.
    if (oldValue === undefined) {
      this.reflectKeysValue = Array.from(new Set(this.url.searchParams.keys()));
    }
  }

  get reflectAll() {
    return this.reflectKeysValue.includes('__all__');
  }

  setParamsFromURL(url: URL) {
    // New params to build the new URL
    const newParams = new URLSearchParams();
    const reflectAll = this.reflectAll;

    const sourceParams = url.searchParams;
    sourceParams.forEach((value, key) => {
      // Skip the key if
      if (
        // it's a Wagtail internal param, or
        key.startsWith('_w_') ||
        // we want to preserve it from the current URL, or
        this.preserveKeysValue.includes(key) ||
        // we don't want to reflect it to the new URL
        (!reflectAll && !this.reflectKeysValue.includes(key))
      ) {
        return;
      }
      newParams.append(key, value);
    });

    // Add the ones we want to preserve from the current URL to the new params
    const currentUrl = this.url;
    currentUrl.searchParams.forEach((value, key) => {
      if (this.preserveKeysValue.includes(key)) {
        newParams.append(key, value);
      }
    });

    currentUrl.search = newParams.toString();
    this.element.setAttribute(this.attrNameValue, currentUrl.toString());
  }

  setParams(event?: CustomEvent<{ requestUrl?: string }>) {
    if (!event) {
      this.setParamsFromURL(new URL(window.location.href));
      return;
    }

    if (!event.detail?.requestUrl) return;

    this.setParamsFromURL(
      new URL(event.detail.requestUrl, window.location.href),
    );
  }
}
