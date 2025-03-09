import { Controller } from '@hotwired/stimulus';
import { slugify } from '../utils/slugify';
import { urlify } from '../utils/urlify';

type SlugMethods = 'slugify' | 'urlify';

/**
 * Adds ability to slugify the value of an input element.
 *
 * @example
 * ```html
 * <input type="text" name="slug" data-controller="w-slug" data-action="blur->w-slug#slugify" />
 * ```
 */
export class SlugController extends Controller<HTMLInputElement> {
  static values = {
    allowUnicode: { default: false, type: Boolean },
  };

  declare allowUnicodeValue: boolean;

  /**
   * Allow for a comparison value to be provided so that a dispatched event can be
   * prevented. This provides a way for other events to interact with this controller
   * to block further updates if a value is not in sync.
   * By default it will compare to the slugify method, this can be overridden by providing
   * either a Stimulus param value on the element or the event's detail.
   */
  compare(
    event: CustomEvent<{ compareAs?: SlugMethods; value: string }> & {
      params?: { compareAs?: SlugMethods };
    },
  ) {
    // do not attempt to compare if the current field is empty
    if (!this.element.value) {
      return true;
    }

    const compareAs =
      event.detail?.compareAs || event.params?.compareAs || 'slugify';

    const compareValue = this[compareAs](
      { detail: { value: event.detail?.value || '' } },
      true,
    );

    const currentValue = this.element.value;

    const valuesAreSame = compareValue.trim() === currentValue.trim();

    if (!valuesAreSame) {
      event?.preventDefault();
    }

    return valuesAreSame;
  }

  /**
   * Basic slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   */
  slugify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    ignoreUpdate = false,
  ) {
    const allowUnicode = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const newValue = slugify(value.trim(), { allowUnicode });

    if (!ignoreUpdate) {
      this.element.value = newValue;
    }

    return newValue;
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
    ignoreUpdate = false,
  ) {
    const allowUnicode = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const trimmedValue = value.trim();

    const newValue =
      urlify(trimmedValue, { allowUnicode }) ||
      this.slugify({ detail: { value: trimmedValue } }, true);

    if (!ignoreUpdate) {
      this.element.value = newValue;
    }

    return newValue;
  }
}
