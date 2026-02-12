import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { castArray } from '../utils/castArray';
import { slugify } from '../utils/slugify';
import { urlify } from '../utils/urlify';

enum Actions {
  Format = 'format',
  Identity = 'identity',
  Slugify = 'slugify',
  Urlify = 'urlify',
}

/**
 * A formatter entry is an array with a regex pattern and an optional replace value.
 */
type FormatterEntry = [(string | [string?, string?])?, string?];

/**
 * Adds ability to clean values of an input element with methods such as `format`, `slugify` or `urlify`.
 *
 * @example - Using the slugify method
 * ```html
 * <input type="text" name="slug" data-controller="w-clean" data-action="blur->w-clean#slugify" />
 * <input type="text" name="slug-with-trim" data-controller="w-clean" data-action="blur->w-clean#slugify" data-w-clean-trim-value="true" />
 * ```
 *
 * @example - Using the urlify method (registered as w-slug)
 * ```html
 * <input type="text" name="url-path" data-controller="w-slug" data-action="change->w-slug#urlify" />
 * <input type="text" name="url-path-with-unicode" data-controller="w-slug" data-w-slug-allow-unicode="true" data-action="change->w-slug#urlify" />
 * <input type="text" name="url-path-with-locale" data-controller="w-slug" data-w-slug-locale="uk-UK" data-action="blur->w-slug#urlify" />
 * ```
 *
 * @example - Using the format method with custom formatters
 * ```html
 * <input type="text" name="no-spaces-or-digits" data-controller="w-clean" data-w-clean-formatters='[["\\s+", ""], ["[^\d-]", ""]]' data-action="blur->w-clean#format" />
 * <input type="text" name="no-yelling" data-controller="w-clean" data-w-clean-formatters='[["!", ""]]' data-action="blur->w-clean#format" />
 * ```
 */
export class CleanController extends Controller<HTMLInputElement> {
  static values = {
    allowUnicode: { default: false, type: Boolean },
    formatters: { default: [], type: Array },
    locale: { default: '', type: String },
    trim: { default: false, type: Boolean },
  };

  /**
   * If true, unicode values in the cleaned values will be allowed.
   * Otherwise unicode values will try to be transliterated.
   * @see `WAGTAIL_ALLOW_UNICODE_SLUGS` in settings
   */
  declare readonly allowUnicodeValue: boolean;
  /** If true, value will be trimmed in all clean methods before being processed by that method. */
  declare readonly trimValue: boolean;
  /** An array of formatter entries with a regex (pattern or pattern & flags array) and an optional replace value. */
  declare readonly formattersValue: FormatterEntry[];
  /** Locale code, used to provide a more specific cleaned value. */
  declare localeValue: string;

  /** Align with the default flags that can be assumed when pulling from Python. */
  defaultRegexFlags = 'gu';
  /** Cache the compiled regex for performance. */
  regexCache: { [key: string]: RegExp } = {};
  /** `und` (undetermined) locale as per ISO 639-2 */
  undeterminedLocale = 'und';

  /**
   * Writes the new value to the element & dispatches the applied event.
   *
   * @fires CleanController#applied - If a change applied to the input value, this event is dispatched.
   *
   * @event CleanController#applied
   * @type {CustomEvent}
   * @property {string} name - `w-slug:applied` | `w-clean:applied`
   * @property {object} detail
   * @property {string} detail.action - The action that was applied (e.g. 'urlify' or 'slugify').
   * @property {string} detail.cleanValue - The the cleaned value that is applied.
   * @property {string} detail.sourceValue - The original value.
   */
  applyUpdate(action: Actions, cleanValue: string, sourceValue?: string) {
    this.element.value = cleanValue;
    this.dispatch('applied', {
      cancelable: false,
      detail: { action, cleanValue, sourceValue },
    });
  }

  /**
   * Allow for a comparison value to be provided so that a dispatched event can be
   * prevented. This provides a way for other events to interact with this controller
   * to block further updates if a value is not in sync.
   * By default it will compare to the slugify method, this can be overridden by providing
   * either a Stimulus param value on the element or the event's detail.
   */
  compare(
    event: CustomEvent<{ compareAs?: Actions; value: string }> & {
      params?: { compareAs?: Actions };
    },
  ) {
    // do not attempt to compare if the field is empty
    if (!this.element.value) return true;

    const compareAs =
      event.detail?.compareAs || event.params?.compareAs || Actions.Slugify;

    const compareValue = this[compareAs](
      { detail: { value: event.detail?.value || '' } },
      { ignoreUpdate: true, runFormat: true },
    );

    const valuesAreSame = this.compareValues(compareValue, this.element.value);

    if (!valuesAreSame) {
      event?.preventDefault();
    }

    return valuesAreSame;
  }

  /**
   * Compares the provided strings, ensuring the values are the same.
   */
  compareValues(...values: string[]): boolean {
    return new Set(values.map((value: string) => `${value}`)).size === 1;
  }

  /**
   * Returns the element's value as is, without any modifications.
   * Useful for identity fields or when no cleaning is required but the event
   * is needed or comparison is required to always pass.
   */
  identity() {
    const action = Actions.Identity;
    const value = this.element.value;
    this.applyUpdate(action, value, value);
    return value;
  }

  /**
   * Formats the source value based on supplied formatters and formatting options.
   * Runs as part of the prepare method on methods called (when used as Stimulus actions)
   * or can be used directly as a standalone action.
   */
  format(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    { ignoreUpdate = false } = {},
  ) {
    const { value: sourceValue = this.element.value } = event?.detail || {};
    if (!sourceValue) return '';

    const cleanValue = this.formattersValue.reduce(
      (val, [regex = [], replaceWith = '']) => {
        const [pattern = '', flags = this.defaultRegexFlags] = castArray(regex);
        return val[flags.includes('g') ? 'replaceAll' : 'replace'](
          this.getRegex(pattern, flags),
          replaceWith,
        );
      },
      this.prepareValue(sourceValue),
    );

    if (!ignoreUpdate) {
      this.applyUpdate(Actions.Format, cleanValue, sourceValue);
    }

    return cleanValue;
  }

  /**
   * Run the format method when the formatters change to ensure
   * that the regex cache is populated with the latest values and
   * that the formatters are valid.
   */
  formattersValueChanged(formatters?: FormatterEntry[]) {
    if (!formatters?.length) return;
    this.regexCache = {};
    try {
      this.format(
        { detail: { value: '__PLACEHOLDER__' } },
        { ignoreUpdate: true },
      );
    } catch (error) {
      this.context.application.handleError(
        error,
        'Invalid regex pattern passed to formatters.',
        { formatters: [...formatters] },
      );
    }
  }

  /**
   * Get a compiled regular expression from the cache or create a new one.
   */
  getRegex(pattern: string, flags: string) {
    const key = [pattern, flags].join(':');
    if (this.regexCache[key]) return this.regexCache[key];
    const regex = new RegExp(pattern, flags);
    this.regexCache[key] = regex;
    return regex;
  }

  /**
   * If the locale is not provided, attempt to find the most suitable target locale:
   * 1. Use the active content locale if available (for translations)
   * 2. Fall back to `und` (undetermined) as per ISO 639-2
   *
   * This only makes a difference when using the `urlify` method and where there are
   * overlapping characters that need to be downcoded but are not in the desired order by default.
   */
  localeValueChanged(currentValue: string) {
    if (currentValue) return;
    this.localeValue =
      WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE || this.undeterminedLocale;
  }

  /**
   * Prepares the value before being processed by an action method.
   * If runFormat is true, it will run the format method on the value.
   */
  prepareValue(sourceValue = '', { runFormat = false } = {}) {
    const value = this.trimValue ? sourceValue.trim() : sourceValue;
    return runFormat
      ? this.format({ detail: { value } }, { ignoreUpdate: true })
      : value;
  }

  /**
   * Basic slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   */
  slugify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    { ignoreUpdate = false, runFormat = !ignoreUpdate } = {},
  ) {
    const { value: sourceValue = this.element.value } = event?.detail || {};
    const preparedValue = this.prepareValue(sourceValue, { runFormat });
    if (!preparedValue) return '';

    const allowUnicode = this.allowUnicodeValue;

    const cleanValue = slugify(preparedValue, { allowUnicode });

    if (!ignoreUpdate) {
      this.applyUpdate(Actions.Slugify, cleanValue, sourceValue);
    }

    return cleanValue;
  }

  /**
   * Advanced slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   *
   * The urlify (Django port) function performs extra processing on the string &
   * is more suitable for creating a slug from the title, rather than sanitizing manually.
   * If the urlify util returns an empty string it will fall back to the slugify method.
   *
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   */
  urlify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    { ignoreUpdate = false, runFormat = !ignoreUpdate } = {},
  ) {
    const { value: sourceValue = this.element.value } = event?.detail || {};
    const preparedValue = this.prepareValue(sourceValue, { runFormat });
    if (!preparedValue) return '';

    const allowUnicode = this.allowUnicodeValue;
    const locale = this.localeValue;

    const cleanValue =
      urlify(preparedValue, { allowUnicode, locale }) ||
      this.slugify(
        { detail: { value: preparedValue } },
        { ignoreUpdate: true },
      );

    if (!ignoreUpdate) {
      this.applyUpdate(Actions.Urlify, cleanValue, sourceValue);
    }

    return cleanValue;
  }
}
