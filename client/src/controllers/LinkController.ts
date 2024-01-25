import { Controller } from '@hotwired/stimulus';

export class LinkController extends Controller<HTMLElement> {
  static values = {
    attrName: { default: 'href', type: String },
    preserveKeys: { default: [], type: Array },
    reflectKeys: { default: ['__all__'], type: Array },
  };

  declare attrNameValue: string;
  declare preserveKeysValue: string[];
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

  setParams(e?: CustomEvent<{ requestUrl?: string }>) {
    if (!e) {
      this.setParamsFromURL(new URL(window.location.href));
      return;
    }

    if (!e.detail?.requestUrl) return;

    this.setParamsFromURL(new URL(e.detail.requestUrl, window.location.href));
  }
}
