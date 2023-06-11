import { Controller } from '@hotwired/stimulus';
import { cleanForSlug } from '../utils/text';

type SlugMethods = 'slugify' | 'urlify';

/**
 * Adds ability to slugify the value of an input element.
 *
 * @example
 * <input type="text" name="slug" data-controller="w-slug" data-action="blur->w-slug#slugify" />
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
    const unicodeSlugsEnabled = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const newValue = cleanForSlug(value.trim(), false, { unicodeSlugsEnabled });

    if (!ignoreUpdate) {
      this.element.value = newValue;
    }

    return newValue;
  }

  /**
   * Advanced slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   */
  urlify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    ignoreUpdate = false,
  ) {
    const unicodeSlugsEnabled = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const newValue = cleanForSlug(value.trim(), true, { unicodeSlugsEnabled });

    if (!ignoreUpdate) {
      this.element.value = newValue;
    }

    return newValue;
  }
}
