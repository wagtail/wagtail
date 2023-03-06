import { Controller } from '@hotwired/stimulus';
import { cleanForSlug } from '../utils/text';

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
   * Allow for a comparison value to be provided, if does not compare to the
   * current value (once transformed), then the event's default will
   * be prevented.
   */
  compare(
    event: CustomEvent<{ value: string }> & { params?: { compareAs?: string } },
  ) {
    // do not attempt to compare if the current field is empty
    if (!this.element.value) {
      return true;
    }

    const {
      detail: { value = '' } = {},
      params: { compareAs = 'slugify' } = {},
    } = event;

    const compareValue = this[compareAs]({ detail: { value } }, true);
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
  slugify(event: CustomEvent<{ value: string }>, ignoreUpdate = false) {
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
  urlify(event: CustomEvent<{ value: string }>, ignoreUpdate = false) {
    const unicodeSlugsEnabled = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const newValue = cleanForSlug(value.trim(), true, { unicodeSlugsEnabled });

    if (!ignoreUpdate) {
      this.element.value = newValue;
    }

    return newValue;
  }
}
