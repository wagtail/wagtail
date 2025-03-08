import $ from 'jquery';

import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

declare global {
  interface JQuery {
    tagit: (options: Record<string, any> | string) => void;
  }
}

/**
 * Attach the jQuery tagit UI to the controlled element.
 *
 * See https://github.com/aehlke/tag-it
 *
 * @example
 * ```html
 * <input id="id_tags" type="text" name="tags" data-controller="w-tag" data-w-tag-url-value="/admin/tag-autocomplete/" />
 * ```
 *
 * @example - With delay
 * ```html
 * <input id="id_tags" type="text" name="tags" data-controller="w-tag" data-w-tag-delay-value="300" data-w-tag-url-value="/admin/tag-autocomplete/" />
 * ```
 */
export class TagController extends Controller {
  static values = {
    delay: { type: Number, default: 0 },
    options: { default: {}, type: Object },
    url: { default: '', type: String },
  };

  /** Options for tagit, see https://github.com/aehlke/tag-it#options */
  declare optionsValue: any;
  /** URL for async tag autocomplete. */
  declare urlValue: string;
  /** Delay to use when debouncing the async tag autocomplete. */
  declare delayValue: number;

  private autocompleteAbort: AbortController | null = null;
  private autocompleteLazy;

  tagit?: JQuery<HTMLElement>;

  initialize() {
    this.autocompleteLazy = debounce(
      this.autocomplete.bind(this),
      this.delayValue,
    );
  }

  connect() {
    const preprocessTag = this.cleanTag.bind(this);

    const autocomplete = {
      source: (request, response) => {
        this.autocompleteLazy.cancel();
        this.autocompleteLazy(request).then(response);
      },
    };

    $(this.element).tagit({
      autocomplete,
      preprocessTag,
      ...this.optionsValue,
    });
  }

  async autocomplete({ term }: { term: string }) {
    if (this.autocompleteAbort) {
      this.autocompleteAbort.abort();
    }

    this.autocompleteAbort = new AbortController();
    const { signal } = this.autocompleteAbort;

    try {
      const url = new URL(this.urlValue, window.location.origin);
      url.searchParams.set('term', term);

      const fetchResponse = await fetch(url.toString(), {
        headers: { Accept: 'application/json' },
        method: 'GET',
        signal,
      });

      const data = await fetchResponse.json();
      return Array.isArray(data) ? data : [];
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        this.context.application.handleError(
          error,
          'Network or API error during autocomplete request.',
          { term, url: this.urlValue },
        );
      }
    } finally {
      this.autocompleteAbort = null;
    }

    return [];
  }

  /**
   * Double quote a tag if it contains a space
   * and if it isn't already quoted.
   */
  cleanTag(val: string) {
    return val && val[0] !== '"' && val.indexOf(' ') > -1 ? `"${val}"` : val;
  }

  /**
   * Method to clear all the tags that are set.
   */
  clear() {
    $(this.element).tagit('removeAll');
  }

  disconnect() {
    if (this.autocompleteAbort) {
      this.autocompleteAbort.abort();
      this.autocompleteAbort = null;
    }
  }
}
