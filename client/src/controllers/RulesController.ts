import { Controller } from '@hotwired/stimulus';

import { castArray } from '../utils/castArray';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a controlled form element to conditionally
 * enable targeted elements based on the data from the controlled form
 * along with a set of rules to match against that data.
 *
 * @example - Enable a button if a value is chosen
 * <form data-controller="w-rules" data-action="change->w-rules#resolve">
 *   <select name="fav-drink" required>
 *     <option value="">Select a drink</option>
 *     <option value="coffee">Coffee</option>
 *     <option value="other">Other</option>
 *   </select>
 *   <button type="button" data-w-rules-target="enable" data-rule='{"fav-drink": ["coffee"]}'>
 *     Continue
 *   </button>
 * </form>
 *
 */
export class RulesController extends Controller<HTMLFormElement> {
  static targets = ['enable'];

  /** Targets will be enabled if the `data-rule` matches the scoped form data, otherwise will be disabled. */
  declare readonly enableTargets: HTMLElement[];
  declare readonly hasEnableTarget: boolean;

  declare active: boolean;
  declare ruleCache: Record<string, Record<string, string[]>>;

  initialize() {
    this.ruleCache = {};
    this.resolve = debounce(this.resolve.bind(this), 50);
  }

  connect() {
    this.checkTargets();
  }

  /**
   * Checks for any targets that will mean that the controller needs to be active.
   */
  checkTargets() {
    this.active = this.hasEnableTarget;
  }

  /**
   * Resolve the conditional targets based on the form data and the target(s)
   * `data-rule` attributes.
   */
  resolve() {
    if (!this.active) return;

    const form = this.element;
    const formData = Object.fromEntries(new FormData(form).entries());

    [
      ...this.enableTargets.map((target) => ({ shouldDisable: false, target })),
    ].forEach(({ shouldDisable, target }) => {
      this.toggleAttribute(
        target,
        this.getIsMatch(formData, this.getRuleData(target))
          ? !shouldDisable
          : shouldDisable,
        'disabled',
      );
    });

    this.dispatch('resolved', { bubbles: true, cancelable: false });
  }

  getIsMatch(
    formData: Record<string, FormDataEntryValue>,
    ruleData: Record<string, string[]>,
  ): boolean {
    return (
      ruleData &&
      Object.entries(ruleData).every(([key, value]) =>
        value.includes(String(formData[key] || '')),
      )
    );
  }

  getRuleData(target: Element): Record<string, string[]> {
    if (!target) return {};
    const ruleStr = target.getAttribute('data-rule');
    if (!ruleStr) return {};

    // check cache
    const cachedRule = this.ruleCache[ruleStr];
    if (cachedRule) return cachedRule;

    // prepare parsed rule data
    let rule = {};

    if (ruleStr) {
      try {
        rule = JSON.parse(ruleStr);
        if (Array.isArray(rule)) rule = Object.fromEntries(rule);
      } catch (e) {
        // Safely ignore JSON parsing errors
      }
    }

    // Map through values and convert to array of strings
    // Allowing falsey values to be treated as an empty string
    const ruleData = Object.fromEntries(
      Object.entries(rule).map(([key, value = null]) => [
        key,
        castArray(value).map((item) => (item ? String(item) : '')),
      ]),
    );

    this.ruleCache[ruleStr] = ruleData;

    return ruleData;
  }

  toggleAttribute(target, shouldRemove = false, attr = 'hidden') {
    if (shouldRemove) {
      target.removeAttribute(attr);
    } else if (attr === 'disabled') {
      // eslint-disable-next-line no-param-reassign
      target.disabled = true;
    } else {
      target.setAttribute(attr, attr);
    }

    // special handling of select fields to avoid selected values from being kept as selected
    if (!(!shouldRemove && target instanceof HTMLOptionElement)) return;
    const selectElement = target.closest('select');

    if (!(selectElement && target.selected)) return;

    const resetValue =
      Array.from(selectElement.options).find((option) => option.defaultSelected)
        ?.value || '';

    selectElement.value = resetValue;

    // intentionally not dispatching a change event, could cause an infinite loop
    this.dispatch('cleared', { bubbles: true, target: selectElement });
  }

  enableTargetDisconnected() {
    this.checkTargets();
  }

  enableTargetConnected() {
    this.active = true;
    this.resolve();
  }
}
