import { Controller } from '@hotwired/stimulus';

import { castArray } from '../utils/castArray';
import { debounce } from '../utils/debounce';

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
export class RulesController extends Controller<HTMLFormElement> {
  static targets = ['enable'];

  /** Targets will be enabled if the target's rule matches the scoped form data, otherwise will be disabled. */
  declare readonly enableTargets: HTMLElement[];
  /** Value set on connect to ensure there are valid targets available, to avoid running rules when not needed. */
  declare readonly hasEnableTarget: boolean;

  declare active: boolean;
  declare rulesCache: Record<string, [string, string[]][]>;

  initialize() {
    this.rulesCache = {};
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
   * rule attributes and the controlled element's form data.
   */
  resolve() {
    if (!this.active) return;

    const formData = new FormData(this.element);

    this.enableTargets.forEach((target) => {
      const shouldEnable = this.findRules(target).every(
        ([fieldName, validValues]) => {
          // reminder that forms can have multiple values for the same field name
          const allFieldValues = formData.getAll(fieldName);
          // reminder that checkbox fields will NOT appear in FormData unless checked
          const fieldValues = allFieldValues.length > 0 ? allFieldValues : [''];
          return validValues.some((validValue) =>
            fieldValues.includes(validValue),
          );
        },
      );

      if (shouldEnable === !target.hasAttribute('disabled')) return;

      if (shouldEnable) {
        target.removeAttribute('disabled');
      } else {
        target.setAttribute('disabled', '');
      }
    });

    this.dispatch('resolved', { bubbles: true, cancelable: false });
  }

  enableTargetDisconnected() {
    this.checkTargets();
  }

  enableTargetConnected() {
    this.active = true;
    this.resolve();
  }

  /**
   * Finds the rules for the provided target by the rules attribute,
   * which is determined via the identifier (e.g. `data-w-rules`).
   * Check the rules cache first, then parse the rules for caching if not found.
   *
   * When parsing the rule, assume an `Object.entries` format or convert an
   * object to this format. Then ensure each value is an array of strings
   * for consistent comparison to FormData values.
   */
  findRules(target: Element) {
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
