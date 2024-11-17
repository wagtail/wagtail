import { Controller } from '@hotwired/stimulus';
import { slugify } from '../utils/slugify';
import { urlify } from '../utils/urlify';

enum Actions {
  Slugify = 'slugify',
  Urlify = 'urlify',
}

/**
 * Adds ability to clean values of an input element with methods such as slugify or urlify.
 *
 * @example - using the slugify method
 * <input type="text" name="slug" data-controller="w-clean" data-action="blur->w-clean#slugify" />
 * <input type="text" name="slug-with-trim" data-controller="w-clean" data-action="blur->w-clean#slugify" data-w-slug-trim-value="true" />
 *
 * @example - using the urlify method (registered as w-slug)
 * <input type="text" name="url-path" data-controller="w-slug" data-action="change->w-slug#urlify" />
 * <input type="text" name="url-path-with-unicode" data-controller="w-slug" data-w-slug-allow-unicode="true" data-action="change->w-slug#urlify" />
 */
export class CleanController extends Controller<HTMLInputElement> {
  static values = {
    allowUnicode: { default: false, type: Boolean },
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

  /**
   * Writes the new value to the element.
   */
  applyUpdate(action: Actions, cleanValue: string) {
    if (action) {
      this.element.value = cleanValue;
    }
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
      { ignoreUpdate: true },
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
   * Prepares the value before being processed by an action method.
   */
  prepareValue(sourceValue = '') {
    const value = this.trimValue ? sourceValue.trim() : sourceValue;
    return value;
  }

  /**
   * Basic slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   */
  slugify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    { ignoreUpdate = false } = {},
  ) {
    const { value: sourceValue = this.element.value } = event?.detail || {};
    const preparedValue = this.prepareValue(sourceValue);
    if (!preparedValue) return '';

    const allowUnicode = this.allowUnicodeValue;

    const cleanValue = slugify(preparedValue, { allowUnicode });

    if (!ignoreUpdate) {
      this.applyUpdate(Actions.Slugify, cleanValue);
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
    { ignoreUpdate = false } = {},
  ) {
    const { value: sourceValue = this.element.value } = event?.detail || {};
    const preparedValue = this.prepareValue(sourceValue);
    if (!preparedValue) return '';

    const allowUnicode = this.allowUnicodeValue;

    const cleanValue =
      urlify(preparedValue, { allowUnicode }) ||
      this.slugify(
        { detail: { value: preparedValue } },
        { ignoreUpdate: true },
      );

    if (!ignoreUpdate) {
      this.applyUpdate(Actions.Urlify, cleanValue);
    }

    return cleanValue;
  }
}
