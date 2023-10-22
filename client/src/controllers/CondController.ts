import { Controller } from '@hotwired/stimulus';

import { castArray } from '../utils/castArray';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a controlled form element to conditionally
 * show/hide targeted elements based on the controlled forms data.
 *
 * @example - Show an additional checkbox if a value is chosen
 * <form data-controller="w-cond" data-action="change->w-cond#resolve">
 *   <select name="fav-drink" required>
 *     <option value="">Select a drink</option>
 *     <option value="coffee">Coffee</option>
 *     <option value="other">Other</option>
 *   </select>
 *   <input type="text" name="other-drink" data-w-cond-target="show" data-match='{"fav-drink": ["other"]}'>
 * </form>
 *
 */
export class CondController extends Controller<HTMLFormElement> {
  static targets = ['show'];

  /** Targets will be shown if the `data-match` matches the scoped form data, otherwise will be hidden. */
  declare readonly showTargets: HTMLElement[];

  declare active: boolean;
  declare matchCache: Record<string, Record<string, string[]>>;

  initialize() {
    this.matchCache = {};
    this.resolve = debounce(this.resolve.bind(this), 50);
  }

  connect() {
    this.checkTargets();
  }

  /**
   * Checks for any targets that will mean that the controller needs to be active.
   */
  checkTargets() {
    this.active = this.showTargets.length > 0;
  }

  /**
   * Resolve the conditional targets based on the form data and the target(s)
   * `data-match` attributes.
   */
  resolve() {
    if (!this.active) return;

    const form = this.element;
    const formData = Object.fromEntries(new FormData(form).entries());

    [
      ...this.showTargets.map((target) => ({ shouldHide: false, target })),
    ].forEach(({ shouldHide, target }) => {
      const isMatch = this.getIsMatch(formData, this.getMatchData(target));
      this.toggleAttribute(target, shouldHide ? !isMatch : isMatch);
    });

    this.dispatch('resolved', { bubbles: true, cancelable: false });
  }

  getIsMatch(
    formData: Record<string, FormDataEntryValue>,
    matchData: Record<string, string[]>,
  ): boolean {
    return (
      matchData &&
      Object.entries(matchData).every(([key, value]) =>
        value.includes(String(formData[key] || '')),
      )
    );
  }

  getMatchData(target: Element): Record<string, string[]> {
    if (!target) return {};
    const matchStr = target.getAttribute('data-match');
    if (!matchStr) return {};

    // check cache
    const cachedMatch = this.matchCache[matchStr];
    if (cachedMatch) return cachedMatch;

    // prepare match data
    let match = {};

    if (matchStr) {
      try {
        match = JSON.parse(matchStr);
        if (Array.isArray(match)) match = Object.fromEntries(match);
      } catch (e) {
        // Safely ignore JSON parsing errors
      }
    }

    // Map through values and convert to array of strings
    // Allowing falsey values to be treated as an empty string
    const matchData = Object.fromEntries(
      Object.entries(match).map(([key, value = null]) => [
        key,
        castArray(value).map((item) => (item ? String(item) : '')),
      ]),
    );

    this.matchCache[matchStr] = matchData;

    return matchData;
  }

  toggleAttribute(target, shouldRemove = false, attr = 'hidden') {
    if (shouldRemove) {
      target.removeAttribute(attr);
    } else if (attr === 'hidden') {
      // eslint-disable-next-line no-param-reassign
      target.hidden = true;
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

  showTargetDisconnected() {
    this.checkTargets();
  }

  showTargetConnected() {
    this.active = true;
    this.resolve();
  }
}
