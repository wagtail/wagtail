/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["disabled"] }] */

import { Controller } from '@hotwired/stimulus';

import { castArray } from '../utils/castArray';
import { debounce } from '../utils/debounce';

/**
 * Form control elements that can support the `disabled` attribute.
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/disabled
 */
type FormControlElement =
  | HTMLButtonElement
  | HTMLFieldSetElement
  | HTMLInputElement
  | HTMLOptGroupElement
  | HTMLOptionElement
  | HTMLSelectElement
  | HTMLTextAreaElement;

/**
 * Adds the ability for a controlled form element to conditionally
 * enable targeted elements based on the data from the controlled form
 * along with a set of rules to match against that data.
 *
 * @example - Enable a button if a specific value is chosen
 * ```html
 * <form data-controller="w-rules" data-action="change->w-rules#resolve">
 *   <select name="fav-drink" required>
 *     <option value="">Select a drink</option>
 *     <option value="coffee">Coffee</option>
 *     <option value="other">Other</option>
 *   </select>
 *   <button type="button" data-w-rules-target="enable" data-w-rules='{"fav-drink": ["coffee"]}'>
 *     Continue
 *   </button>
 * </form>
 * ```
 */
export class RulesController extends Controller<
  HTMLFormElement | FormControlElement
> {
  static targets = ['enable'];

  /** Targets will be enabled if the target's rule matches the scoped form data, otherwise will be disabled. */
  declare readonly enableTargets: FormControlElement[];
  /** True if there is at least one enable target, used to ensure rules do not run if not needed. */
  declare readonly hasEnableTarget: boolean;

  declare form;
  declare rulesCache: Record<string, [string, string[]][]>;

  initialize() {
    this.rulesCache = {};
    this.resolve = debounce(this.resolve.bind(this), 50);

    const element = this.element;
    if (element instanceof HTMLFormElement) {
      this.form = element;
    } else if ('form' in element) {
      this.form = element.form;
    } else {
      this.form = element.closest('form');
    }
  }

  /**
   * Resolve the conditional targets based on the form data and the target(s)
   * rule attributes and the controlled element's form data.
   */
  resolve() {
    if (!this.hasEnableTarget) return;

    const formData = new FormData(this.form);

    this.enableTargets.forEach((target) => {
      const rules = this.parseRules(target);

      const enable = rules.every(([fieldName, allowedValues]) => {
        // Forms can have multiple values for the same field name
        const values = formData.getAll(fieldName);
        // Checkbox fields will NOT appear in FormData unless checked, support this when validValues are also empty
        if (allowedValues.length === 0 && values.length === 0) return true;
        return allowedValues.some((validValue) => values.includes(validValue));
      });

      if (enable === !target.disabled) return;

      const event = this.dispatch('effect', {
        bubbles: true,
        cancelable: true,
        detail: { effect: 'enable', enable },
        target,
      });

      if (!event.defaultPrevented) {
        target.disabled = !enable;
      }
    });

    this.dispatch('resolved', { bubbles: true, cancelable: false });
  }

  enableTargetDisconnected() {
    this.resolve();
  }

  enableTargetConnected() {
    this.resolve();
  }

  /**
   * Finds & parses the rules for the provided target by the rules attribute,
   * which is determined via the identifier (e.g. `data-w-rules`).
   * Check the rules cache first, then parse the rules for caching if not found.
   *
   * When parsing the rule, assume an `Object.entries` format or convert an
   * object to this format. Then ensure each value is an array of strings
   * for consistent comparison to FormData values.
   */
  parseRules(target: Element) {
    if (!target) return [];
    const rulesRaw = target.getAttribute(`data-${this.identifier}`);
    if (!rulesRaw) return [];

    const cachedRule = this.rulesCache[rulesRaw];
    if (cachedRule) return cachedRule;

    let parsedRules;

    try {
      parsedRules = JSON.parse(rulesRaw);
    } catch (error) {
      this.context.handleError(error, 'Unable to parse rule.');
      return [];
    }

    const rules = (
      Array.isArray(parsedRules) ? parsedRules : Object.entries(parsedRules)
    )
      .filter(Array.isArray)
      .map(([fieldName = '', validValues = ''] = []) => [
        fieldName,
        castArray(validValues).map(String),
      ]) as [string, string[]][];

    this.rulesCache[rulesRaw] = rules;

    return rules;
  }
}
