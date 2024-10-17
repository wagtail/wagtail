import { Controller } from '@hotwired/stimulus';
import { slugify } from '../utils/slugify';
import { urlify } from '../utils/urlify';

type ValidMethods = 'slugify' | 'urlify';

/**
 * Adds ability to clean values of an input element with methods such as slugify or urlify.
 *
 * @example - using the slugify method
 * <input type="text" name="slug" data-controller="w-clean" data-action="blur->w-clean#slugify" />
 *
 * @example - using the urlify method (registered as w-slug)
 * <input type="text" name="url-path" data-controller="w-slug" data-action="change->w-slug#urlify" />
 */
export class CleanController extends Controller<HTMLInputElement> {
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
  async compare(
    event: CustomEvent<{ compareAs?: ValidMethods; value: string }> & {
      params?: { compareAs?: ValidMethods };
    },
  ) {
    // do not attempt to compare if the current field is empty
    if (!this.element.value) {
      return true;
    }

    const compareAs =
      event.detail?.compareAs || event.params?.compareAs || 'slugify';

    const compareValue = await this[compareAs](
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
   *
   * @fires CleanController#slugify - Dispatched before the value is updated, allows for custom processing.
   *
   * @event CleanController#slugify
   * @type {CustomEvent}
   * @property {boolean} cancelable - Is cancelable
   * @property {function} detail.continue - Continue with a custom cleaned value
   * @property {string} detail.value - The original value
   * @property {string} detail.valueCleaned - The cleaned value
   * @property {string} name - `w-clean:slugify` or `w-slug:slugify`
   */
  async slugify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    ignoreUpdate = false,
  ) {
    const allowUnicode = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};
    const valueCleaned = slugify(value.trim(), { allowUnicode });

    const resolvedValue = await new Promise<string>((resolve) => {
      const overrideEvent = this.dispatch('slugify', {
        bubbles: true,
        cancelable: true,
        detail: {
          allowUnicode,
          continue: (_: unknown) => resolve(String(_)),
          value,
          valueCleaned,
        },
      });
      if (!overrideEvent.defaultPrevented) resolve(valueCleaned);
    });

    if (!ignoreUpdate) {
      this.element.value = resolvedValue;
    }

    return resolvedValue;
  }

  /**
   * Advanced slugify of a string, updates the controlled element's value
   * or can be used to simply return the transformed value.
   *
   * The urlify (Django port) function performs extra processing on the string &
   * is more suitable for creating a slug from the title, rather than sanitising manually.
   * If the urlify util returns an empty string it will fall back to the slugify method.
   *
   * If a custom event with detail.value is provided, that value will be used
   * instead of the field's value.
   *
   * @fires CleanController#urlify - Dispatched before the value is updated, allows for custom processing.
   *
   * @event CleanController#urlify
   * @type {CustomEvent}
   * @property {boolean} cancelable - Is cancelable
   * @property {function} detail.continue - Continue with a custom cleaned value
   * @property {string} detail.value - The original value
   * @property {string} detail.valueCleaned - The cleaned value
   * @property {string} name - `w-clean:urlify` or `w-slug:urlify`
   */
  async urlify(
    event: CustomEvent<{ value: string }> | { detail: { value: string } },
    ignoreUpdate = false,
  ) {
    const allowUnicode = this.allowUnicodeValue;
    const { value = this.element.value } = event?.detail || {};

    const valueCleaned =
      urlify(value.trim(), { allowUnicode }) ||
      this.slugify({ detail: { value } }, true);

    const resolvedValue = await new Promise<string>((resolve) => {
      const overrideEvent = this.dispatch('urlify', {
        bubbles: true,
        cancelable: true,
        detail: {
          allowUnicode,
          continue: (_: unknown) => resolve(String(_)),
          value,
          valueCleaned,
        },
      });
      if (!overrideEvent.defaultPrevented) resolve(valueCleaned);
    });

    if (!ignoreUpdate) {
      this.element.value = resolvedValue;
    }

    return resolvedValue;
  }
}
