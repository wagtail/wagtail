import { Controller } from '@hotwired/stimulus';

/**
 * Adds the ability for the controlled element to reflect the URL's query parameters
 * from an event or the current URL into the window.location so that dynamic updates
 * to listings can be available on refreshing or other internal links.
 *
 * @example - Reflecting the URL's query parameters
 * <a href="/?q=1" data-controller="w-link" data-w-link-reflect-keys-value="['q']"></a>
 */
export class LinkController extends Controller<HTMLElement> {
  static values = {
    attrName: { default: 'href', type: String },
    preserveKeys: { default: [], type: Array },
    reflectKeys: { default: ['__all__'], type: Array },
  };

  /** Attribute on the controlled element containing the URL string. */
  declare attrNameValue: string;
  /** URL param keys that will be kept in the current location's URL. */
  declare preserveKeysValue: string[];
  /** URL param keys to be added to the location URL from the source URL. */
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
