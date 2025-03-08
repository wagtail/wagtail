import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Allow for an element to trigger an async query that will
 * patch the results into a results DOM container. The controlled
 * element can be the query input, the containing form, or a button.
 * It supports the ability to update the URL with the query
 * when processed or simply make a query based on a form's
 * values.
 *
 * @example - A form that will update the results based on the form's input
 * ```html
 * <div id="results"></div>
 * <form
 *   data-controller="w-swap"
 *   data-action="input->w-swap#submitLazy"
 *   data-w-swap-src-value="path/to/search"
 *   data-w-swap-target-value="#results"
 * >
 *   <input id="search" type="text" name="query" />
 *   <input id="filter" type="text" name="filter" />
 * </form>
 * ```
 *
 * @example - A single input that will update the results & the URL
 * ```html
 * <div id="results"></div>
 * <input
 *   id="search"
 *   type="text"
 *   name="q"
 *   data-controller="w-swap"
 *   data-action="input->w-swap#searchLazy"
 *   data-w-swap-src-value="path/to/search"
 *   data-w-swap-target-value="#listing-results"
 * />
 * ```
 *
 * @example - A single button that will update the results
 * ```html
 * <div id="results"></div>
 * <button
 *   id="clear"
 *   data-controller="w-swap"
 *   data-action="input->w-swap#replaceLazy"
 *   data-w-swap-src-value="path/to/results/?type=bar"
 *   data-w-swap-target-value="#results"
 * >
 *   Clear owner filter
 * </button>
 * ```
 */
export class SwapController extends Controller<
  HTMLFormElement | HTMLInputElement | HTMLButtonElement
> {
  static defaultClearParam = 'p';

  static targets = ['input'];

  static values = {
    icon: { default: '', type: String },
    loading: { default: false, type: Boolean },
    reflect: { default: false, type: Boolean },
    defer: { default: false, type: Boolean },
    src: { default: '', type: String },
    jsonPath: { default: '', type: String },
    target: { default: '#listing-results', type: String },
    wait: { default: 200, type: Number },
  };

  declare readonly hasInputTarget: boolean;
  declare readonly hasTargetValue: boolean;
  declare readonly hasUrlValue: boolean;
  declare readonly hasJsonPathValue: boolean;
  declare readonly inputTarget: HTMLInputElement;

  declare iconValue: string;
  declare loadingValue: boolean;
  declare reflectValue: boolean;
  /** Defer writing the results while there is interaction with the target container */
  declare deferValue: boolean;
  declare srcValue: string;
  /** A dotted path to the HTML string value to extract from the JSON response */
  declare jsonPathValue: string;
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
  /** Debounced function to submit the serialized form and then replace the DOM */
  submitLazy?: { (...args: any[]): void; cancel(): void };
  /** A function that writes the HTML to the target */
  writeDeferred?: () => Promise<string>;

  connect() {
    this.srcValue =
      this.srcValue || this.formElement.getAttribute('action') || '';
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
    // Don't bother marking as busy and adding the spinner icon if we defer writes
    if (this.deferValue) return;

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

  get formElement() {
    return (
      this.hasInputTarget ? this.inputTarget.form || this.element : this.element
    ) as HTMLFormElement;
  }

  /**
   * Update the target element's content with the response from a request based on the input's form
   * values serialized. Do not account for anything in the main location/URL, simply replace the content within
   * the target element.
   */
  submit() {
    const form = this.formElement;
    let data: FormData | undefined = new FormData(form);

    let url = this.srcValue;
    // serialize the form to a query string if it's a GET request
    if (form.getAttribute('method')?.toUpperCase() === 'GET') {
      // cast as any to avoid https://github.com/microsoft/TypeScript/issues/43797
      url += '?' + new URLSearchParams(data as any).toString();
      data = undefined;
    }

    this.replace(url, data);
  }

  reflectParams(url: string) {
    const params = new URL(url, window.location.href).searchParams;
    const filteredParams = new URLSearchParams();
    params.forEach((value, key) => {
      // Check if the value is not empty after trimming white space
      // and if the key is not a Wagtail internal param
      if (value.trim() !== '' && !key.startsWith('_w_')) {
        filteredParams.append(key, value);
      }
    });
    const queryString = `?${filteredParams.toString()}`;
    window.history.replaceState(null, '', queryString);
  }

  /**
   * Abort any existing requests & set up new abort controller, then fetch and replace
   * the HTML target with the new results.
   * Cancel any in progress results request using the AbortController so that
   * a faster response does not replace an in flight request.
   */
  async replace(
    urlSource?:
      | string
      | (CustomEvent<{ url: string }> & { params?: { url?: string } }),
    data?: FormData,
  ) {
    const target = this.target;
    /** Parse a request URL from the supplied param, as a string or inside a custom event */
    const requestUrl =
      (typeof urlSource === 'string'
        ? urlSource
        : urlSource?.detail?.url || urlSource?.params?.url || '') ||
      this.srcValue;

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
    const formMethod =
      this.formElement.getAttribute('method')?.toUpperCase() || 'GET';
    return fetch(requestUrl, {
      headers: {
        'x-requested-with': 'XMLHttpRequest',
        [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      },
      signal,
      method: formMethod,
      body: formMethod !== 'GET' ? data : undefined,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // Allow support for expecting a JSON response that contains the HTML
        // fragment at a specific path. This allows the backend to return a JSON
        // response that also contains other data (e.g. state updates), which can
        // be easier to work with in JS compared to inspecting the HTML directly.
        if (this.jsonPathValue) {
          let html: unknown;
          try {
            const json: Record<string, unknown> = await response.json();

            // Dispatch an event with the JSON data to allow other controllers to
            // access the data and potentially modify it before extracting the HTML.
            this.dispatch('json', {
              cancelable: false,
              detail: { requestUrl, data: json },
            });

            html = this.jsonPathValue
              .split('.')
              .reduce<unknown>(
                (acc, key) => (acc as Record<string, unknown>)[key],
                json,
              );
          } catch {
            html = undefined;
          }

          if (typeof html !== 'string') {
            throw new Error(
              `Unable to parse as JSON at path "${this.jsonPathValue}" to a string`,
            );
          }
          return html;
        }
        return response.text();
      })
      .then((results) => {
        const write = async () => {
          // If there's a previously deferred write, which may or may not be
          // this current function, clear it and proceed with the current one.
          this.writeDeferred = undefined;
          target.innerHTML = results;

          if (this.reflectValue) {
            const event = this.dispatch('reflect', {
              cancelable: true,
              detail: { requestUrl },
              target,
            });
            if (!event.defaultPrevented) {
              this.reflectParams(requestUrl);
            }
          }

          this.dispatch('success', {
            cancelable: false,
            detail: { requestUrl, results },
            target,
          });

          return results;
        };

        // If the currently focused element is within the target container,
        // or if there's a tooltip present, defer the write until the focus has
        // left the container or all tooltips have been removed.
        const tooltipSelector =
          '[aria-expanded="true"], [aria-describedby^="tippy"]';
        const hasFocus =
          document.activeElement && target.contains(document.activeElement);
        const hasTooltip = target.querySelector(tooltipSelector);

        if (this.deferValue && (hasFocus || hasTooltip)) {
          return new Promise((resolve, reject) => {
            this.writeDeferred = write;

            const tryWrite = () => {
              if (this.writeDeferred) {
                // This function is called both when the focus leaves the target
                // container and when all tooltips are removed. They are not
                // mutually exclusive and are called separately, so we need to
                // check both conditions to ensure we don't write when the other
                // condition is still true.
                const nowHasFocus =
                  document.activeElement &&
                  target.contains(document.activeElement);
                const nowHasTooltip = target.querySelector(tooltipSelector);

                // Return false to indicate that we still need to defer the write
                if (nowHasFocus || nowHasTooltip) return false;

                this.writeDeferred().then(resolve).catch(reject);
              } else {
                // The deferred write has been cleared but this listener is still
                // triggered, which is unlikely to happen but possible
                // (e.g. another request was made but the focus is still here and
                // deferValue is set to false), so just resolve
                resolve(results);
              }

              // Return true to indicate that we're done deferring
              // and the listener/observer should be cleaned up
              return true;
            };

            if (hasFocus) {
              const handleFocusOut = (event: FocusEvent) => {
                // If the new focus is still within the target container, do nothing
                if (target.contains(event.relatedTarget as Node | null)) return;

                const done = tryWrite();
                if (done) {
                  target.removeEventListener('focusout', handleFocusOut);
                }
              };
              target.addEventListener('focusout', handleFocusOut);
            }

            // Not using `else` here because hasFocus and hasTooltip are not
            // mutually exclusive
            if (hasTooltip) {
              // Tooltips may be triggered by other events (e.g. mouseenter, click).
              // Instead of using events, we use a MutationObserver to detect if
              // there are any tooltips present in the target container.

              const callback: MutationCallback = (_, observer) => {
                const done = tryWrite();
                if (done) {
                  observer.disconnect();
                }
              };

              const observer = new MutationObserver(callback);
              observer.observe(target, {
                attributeFilter: ['aria-expanded', 'aria-describedby'],
                subtree: true,
              });
            }
          });
        }

        return write();
      })
      .catch((error) => {
        if (signal.aborted) return;
        this.dispatch('error', {
          cancelable: false,
          detail: { error, requestUrl },
          target,
        });
        // eslint-disable-next-line no-console
        console.error('Error fetching %s', requestUrl, error);
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
