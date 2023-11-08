import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';

/**
 * Allow for an element to trigger an async query that will
 * patch the results into a results DOM container. The query
 * input can be the controlled element or the containing form.
 * It supports the ability to update the URL with the query
 * when processed or simply make a query based on a form's
 * values.
 *
 * @example - A form that will update the results based on the form's input
 *  <div id="results"></div>
 *  <form
 *    data-controller="w-swap"
 *    data-action="input->w-swap#submitLazy"
 *    data-w-swap-src-value="path/to/search"
 *    data-w-swap-target-value="#results"
 *  >
 *  <input id="search" type="text" name="query" />
 *  <input id="filter" type="text" name="filter" />
 * </form>
 *
 * @example - A single input that will update the results & the URL
 *  <div id="results"></div>
 *  <input
 *    id="search"
 *    type="text"
 *    name="q"
 *    data-controller="w-swap"
 *    data-action="input->w-swap#searchLazy"
 *    data-w-swap-src-value="path/to/search"
 *    data-w-swap-target-value="#listing-results"
 *  />
 *
 */
export class SwapController extends Controller<
  HTMLFormElement | HTMLInputElement
> {
  static defaultClearParam = 'p';

  static targets = ['input'];

  static values = {
    icon: { default: '', type: String },
    loading: { default: false, type: Boolean },
    src: { default: '', type: String },
    target: { default: '#listing-results', type: String },
    wait: { default: 200, type: Number },
  };

  declare readonly hasInputTarget: boolean;
  declare readonly hasTargetValue: boolean;
  declare readonly hasUrlValue: boolean;
  declare readonly inputTarget: HTMLInputElement;

  declare iconValue: string;
  declare loadingValue: boolean;
  declare srcValue: string;
  declare targetValue: string;
  declare waitValue: number;

  /** Allow cancelling of in flight async request if disconnected */
  abortController?: AbortController;
  /** The related icon element to attach the spinner to */
  iconElement?: SVGUseElement | null;
  /** Debounced function to request a URL and then replace the DOM with the results */
  replaceLazy?: { (...args: any[]): void; cancel(): void };
  /** Debounced function to search results and then replace the DOM */
  searchLazy?: { (...args: any[]): void; cancel(): void };
  /** Debounced function to submit the serialised form and then replace the DOM */
  submitLazy?: { (...args: any[]): void; cancel(): void };

  connect() {
    const formContainer = this.hasInputTarget
      ? this.inputTarget.form
      : this.element;
    this.srcValue =
      this.srcValue || formContainer?.getAttribute('action') || '';
    const target = this.target;

    // set up icons
    this.iconElement = null;
    const iconContainer = (
      this.hasInputTarget ? this.inputTarget : this.element
    ).parentElement;

    this.iconElement = iconContainer?.querySelector('use') || null;
    this.iconValue = this.iconElement?.getAttribute('href') || '';

    // set up initial loading state (if set originally in the HTML)
    this.loadingValue = false;

    // set up debounced methods
    this.replaceLazy = debounce(this.replace.bind(this), this.waitValue);
    this.searchLazy = debounce(this.search.bind(this), this.waitValue);
    this.submitLazy = debounce(this.submit.bind(this), this.waitValue);

    // dispatch event for any initial action usage
    this.dispatch('ready', { cancelable: false, target });
  }

  /**
   * Element that receives the fetch result HTML output
   */
  get target() {
    const targetValue = this.targetValue;
    const targetElement = document.querySelector(targetValue);

    const foundTarget = targetElement && targetElement instanceof HTMLElement;
    const hasValidUrlValue = !!this.srcValue;

    const errors: string[] = [];

    if (!foundTarget) {
      errors.push(`Cannot find valid target element at "${targetValue}"`);
    }

    if (!hasValidUrlValue) {
      errors.push(`Cannot find valid src URL value`);
    }

    if (errors.length) {
      throw new Error(errors.join(', '));
    }

    return targetElement as HTMLElement;
  }

  /**
   * Toggle the visual spinner icon if available and ensure content about
   * to be replaced is flagged as busy.
   */
  loadingValueChanged(isLoading: boolean, isLoadingPrevious) {
    const target = isLoadingPrevious === undefined ? null : this.target; // ensure we avoid DOM interaction before connect
    if (isLoading) {
      target?.setAttribute('aria-busy', 'true');
      this.iconElement?.setAttribute('href', '#icon-spinner');
    } else {
      target?.removeAttribute('aria-busy');
      this.iconElement?.setAttribute('href', this.iconValue);
    }
  }

  /**
   * Perform a URL search param update based on the input's value with a comparison against the
   * matching URL search params. Will replace the target element's content with the results
   * of the async search request based on the query.
   *
   * Search will only be performed with the URL param value is different to the input value.
   * Cleared params will be removed from the URL if present.
   *
   * `clear` can be provided as Event detail or action param to override the default of 'p'.
   */
  search(
    data?: CustomEvent<{ clear: string }> & {
      params?: { clear?: string };
    },
  ) {
    /** Params to be cleared when updating the location (e.g. ['p'] for page). */
    const clearParams = (
      data?.detail?.clear ||
      data?.params?.clear ||
      (this.constructor as typeof SwapController).defaultClearParam
    ).split(' ');

    const searchInput = this.hasInputTarget ? this.inputTarget : this.element;
    const queryParam = searchInput.name;
    const searchParams = new URLSearchParams(window.location.search);
    const currentQuery = searchParams.get(queryParam) || '';
    const newQuery = searchInput.value || '';

    // only do the query if it has changed for trimmed queries
    // for example - " " === "" and "first word " ==== "first word"
    if (currentQuery.trim() === newQuery.trim()) return;

    // Update search query param ('q') to the new value or remove if empty
    if (newQuery) {
      searchParams.set(queryParam, newQuery);
    } else {
      searchParams.delete(queryParam);
    }

    // clear any params (e.g. page/p) if needed
    clearParams.forEach((param) => {
      searchParams.delete(param);
    });

    const queryString = '?' + searchParams.toString();
    const url = this.srcValue;

    this.replace(url + queryString).then(() => {
      window.history.replaceState(null, '', queryString);
    });
  }

  /**
   * Update the target element's content with the response from a request based on the input's form
   * values serialised. Do not account for anything in the main location/URL, simply replace the content within
   * the target element.
   */
  submit() {
    const form = (
      this.hasInputTarget ? this.inputTarget.form : this.element
    ) as HTMLFormElement;

    // serialise the form to a query string
    // https://github.com/microsoft/TypeScript/issues/43797
    const searchParams = new URLSearchParams(new FormData(form) as any);

    const queryString = '?' + searchParams.toString();
    const url = this.srcValue;

    this.replace(url + queryString);
  }

  /**
   * Abort any existing requests & set up new abort controller, then fetch and replace
   * the HTML target with the new results.
   * Cancel any in progress results request using the AbortController so that
   * a faster response does not replace an in flight request.
   */
  async replace(
    data?:
      | string
      | (CustomEvent<{ url: string }> & { params?: { url?: string } }),
  ) {
    const target = this.target;
    /** Parse a request URL from the supplied param, as a string or inside a custom event */
    const requestUrl =
      (typeof data === 'string'
        ? data
        : data?.detail?.url || data?.params?.url || '') || this.srcValue;

    if (this.abortController) this.abortController.abort();
    this.abortController = new AbortController();
    const { signal } = this.abortController;

    this.loadingValue = true;

    const beginEvent = this.dispatch('begin', {
      cancelable: true,
      detail: { requestUrl },
      target: this.target,
    }) as CustomEvent<{ requestUrl: string }>;

    if (beginEvent.defaultPrevented) return Promise.resolve();

    return fetch(requestUrl, {
      headers: { 'x-requested-with': 'XMLHttpRequest' },
      signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.text();
      })
      .then((results) => {
        target.innerHTML = results;
        this.dispatch('success', {
          cancelable: false,
          detail: { requestUrl, results },
          target,
        });
        return results;
      })
      .catch((error) => {
        if (signal.aborted) return;
        this.dispatch('error', {
          cancelable: false,
          detail: { error, requestUrl },
          target,
        });
        // eslint-disable-next-line no-console
        console.error(`Error fetching ${requestUrl}`, error);
      })
      .finally(() => {
        if (signal === this.abortController?.signal) {
          this.loadingValue = false;
        }
      });
  }

  /**
   * When disconnecting, ensure we reset any visual related state values and
   * cancel any in-flight requests.
   */
  disconnect() {
    this.loadingValue = false;
    this.replaceLazy?.cancel();
    this.searchLazy?.cancel();
    this.submitLazy?.cancel();
  }
}
