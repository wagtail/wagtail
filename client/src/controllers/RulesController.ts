import { Controller } from '@hotwired/stimulus';

import { castArray } from '../utils/castArray';
import { debounce } from '../utils/debounce';

/**
 * Enum for the different effects that can be applied to form controls,
 * determined by the different controller targets and rules.
 */
enum Effect {
  Enable = 'enable',
  Show = 'show',
}

/**
 * Match values determine how rules are resolved from the form data
 * to determine if the rule has been satisfied.
 *
 * @remarks
 * Match values are inspired by JSON Schema's `allOf`, `anyOf`, `oneOf`, and `not` keywords,
 * @see https://json-schema.org/understanding-json-schema/reference/combining
 */
enum Match {
  All = 'all', // Default
  Any = 'any',
  Not = 'not',
  One = 'one',
}

type RuleEntry = [string, string[]];

type EffectHandler = (
  target: FormControlElement | HTMLElement,
  result: boolean,
) => (() => void) | null;

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
 * enable or show targeted elements based on the data from the controlled form
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
 *
 * @example - Show an additional field when a select field value is chosen
 * ```html
 * <form data-controller="w-rules" data-action="change->w-rules#resolve">
 *   <select name="fav-drink" required>
 *     <option value="">Select a drink</option>
 *     <option value="coffee">Coffee</option>
 *     <option value="other">Other</option>
 *   </select>
 *   <input type="text" name="other-drink" data-w-rules-target="show" data-w-rules='{"fav-drink": ["other"]}'>
 * </form>
 * ```
 *
 * @example - Use match to apply different sets of rules
 * <form data-controller="w-rules" data-action="change->w-rules#resolve">
 *   <input type="file" id="avatar" name="avatar" accept="image/png, image/jpeg">
 *   <input type="email" id="email" name="email" required>
 *   <output name="summary" for="file email">
 *     <span data-w-rules='{"avatar": [""], "email": [""]}' data-w-rules-match="not" data-w-rules-target="show">Your profile details are ready.</span>
 *     <span data-w-rules='{"avatar": [""], "email": [""]}' data-w-rules-match="any" data-w-rules-target="show">Your profile details are missing.</span>
 *   </output>
 * </form>
 * ```
 */
export class RulesController extends Controller<
  HTMLFormElement | FormControlElement
> {
  static targets = ['enable', 'show'];

  static values = {
    match: { default: Match.All, type: String },
  };

  /** The matching strategy to use for the rules, defaults to `all` and used as the fallback if not provided. */
  declare readonly matchValue: Match;

  /** Targets will be enabled if the target's rule matches the scoped form data, otherwise will be disabled. */
  declare readonly enableTargets: FormControlElement[];
  /** True if there is at least one enable target, used to ensure rules do not run if not needed. */
  declare readonly hasEnableTarget: boolean;
  /** Targets will be shown if the target's rule matches the scoped form data, otherwise will be hidden with the `hidden` attribute. */
  declare readonly showTargets: HTMLElement[];
  /** True if there is at least one show target, used to ensure rules do not run if not needed. */
  declare readonly hasShowTarget: boolean;

  declare formCache: HTMLFormElement | null;
  declare rulesCache: Record<string, RuleEntry[]>;

  initialize() {
    this.rulesCache = {};
    this.resolve = debounce(this.resolve.bind(this), 50);
  }

  /**
   * Cache the form element found on the controller to avoid
   * DOM thrashing when multiple resolves happen.
   */
  get form() {
    if (this.formCache) return this.formCache;
    const element = this.element;
    if (element instanceof HTMLFormElement) {
      this.formCache = element;
    } else {
      const form = 'form' in element ? element.form : element.closest('form');
      if (form) {
        this.formCache = form;
      }
    }
    if (this.formCache) return this.formCache;
    throw new Error('Form not found.');
  }

  /**
   * Effect targets grouped by effect type.
   */
  get effectTargets() {
    return {
      [Effect.Enable]: this.enableTargets,
      [Effect.Show]: this.showTargets,
    } as const;
  }

  /**
   * Effect handlers to first determine if the effect needs to be applied,
   * if it does, it will return a function to apply the effect.
   */
  get effectHandlers(): Record<Effect, EffectHandler> {
    return {
      [Effect.Enable]: (target, result) => {
        if (!('disabled' in target)) return null;
        if (result === !target.disabled) return null;
        return () => {
          target.disabled = !result;
        };
      },
      [Effect.Show]: (target, result) => {
        if (result === !target.hidden) return null;
        return () => {
          target.hidden = !result;
        };
      },
    } as const;
  }

  /**
   * Returns an object of match functions that will be used to match against
   * the current state of the form data.
   */
  get matchers(): Record<Match, (rules: RuleEntry[]) => boolean> {
    const checkFn = ([fieldName, allowedValues]) => {
      // Forms can have multiple values for the same field name
      const values = new FormData(this.form).getAll(fieldName);
      // Checkbox fields will NOT appear in FormData unless checked, support this when validValues are also empty
      if (allowedValues.length === 0 && values.length === 0) return true;
      return allowedValues.some((validValue) => values.includes(validValue));
    };

    return {
      [Match.All]: (rules) => rules.every(checkFn),
      [Match.Any]: (rules) => rules.some(checkFn),
      [Match.Not]: (rules) => rules.filter(checkFn).length === 0,
      [Match.One]: (rules) => rules.filter(checkFn).length === 1,
    };
  }

  /**
   * Resolve the conditional targets based on the form data and the target(s)
   * rule attributes and the controlled element's form data.
   *
   * For each effect target, determine the match type to use, parse the rules,
   * run the matchers and apply the effect if needed.
   *
   * An `effect` event is dispatched before applying the effect,
   * which can be cancelled to prevent the effect from being applied.
   *
   * Finally, a `resolved` event is dispatched after all effects have been processed.
   */
  resolve(event?: Event & { params?: { match?: Match } }) {
    if (!this.hasEnableTarget && !this.hasShowTarget) return;

    const effectHandlers = this.effectHandlers;
    const effectTargets = this.effectTargets;
    const matchers = this.matchers;

    Object.entries(effectTargets).forEach(([effect, targets]) => {
      targets.forEach((target) => {
        const match = this.getMatchType(target, effect as Effect, event);
        const rules = this.parseRules(target, effect as Effect);
        const result = matchers[match](rules);
        const apply = effectHandlers[effect](target, result);

        if (!apply) return;

        const effectEvent = this.dispatch('effect', {
          bubbles: true,
          cancelable: true,
          detail: { effect, [effect]: result },
          target,
        });

        if (effectEvent.defaultPrevented) return;

        apply();

        // special handling of select fields to avoid selected values from being kept as selected
        if (!result && target instanceof HTMLOptionElement && target.selected) {
          const select = target.closest('select');
          if (!select) return;

          const resetValue =
            Array.from(select.options).find((option) => option.defaultSelected)
              ?.value || '';

          const currentValue = select.value;

          // Do nothing if the current value is the reset value to avoid 'change' event loops
          if (currentValue === resetValue) return;

          select.value = resetValue;

          // dispatch change event (on select)
          this.dispatch('change', {
            prefix: '',
            target: select,
            bubbles: true,
            cancelable: false,
          });
        }
      });
    });

    this.dispatch('resolved', { bubbles: true, cancelable: false });
  }

  /**
   * Get the match type for the specified target, effect or event
   * so that the most specific match value can be used for this rules
   * resolving.
   *
   * First check the event for provided params, then the target element
   * for attributes, finally the controller's match value with default
   * and error handling for edge cases.
   */
  getMatchType(
    target: Element,
    effect: Effect = Effect.Enable,
    { params = {} }: { params?: { match?: Match } } = {},
  ): Match {
    const identifier = this.identifier;
    const matchValues = Object.values(Match);
    return [
      params.match,
      target.getAttribute(`data-${identifier}-${effect}-match`) ||
        target.getAttribute(`data-${identifier}-match`),
      this.matchValue,
      Match.All, // ensure there's always a default value if all others are blank
    ].find((value): value is Match => {
      if (!value || typeof value !== 'string') return false;
      if (matchValues.includes(value as Match)) return true;
      this.context.handleError(
        new Error(`Invalid match value: '${value}'.`),
        `Match value must be one of: '${matchValues.join("', '")}'.`,
      );
      return false;
    })!;
  }

  /**
   * Finds & parses the rules for the provided target by the rules attribute,
   * which is determined via the identifier and the provided effect name,
   * (e.g. `data-w-rules-enable`). Falling back to the generic attribute
   * if not found (e.g. `data-w-rules`).
   *
   * With the found rules, check the rules cache first,
   * then parse the rules for caching if not found.
   *
   * When parsing the rule, assume an `Object.entries` format or convert an
   * object to this format. Then ensure each value is an array of strings
   * for consistent comparison to FormData values.
   */
  parseRules(target: Element, effect: Effect = Effect.Enable): RuleEntry[] {
    if (!target) return [];

    let attribute = `data-${this.identifier}-${effect}`;
    let rulesRaw = target.getAttribute(attribute);

    if (!rulesRaw) {
      attribute = `data-${this.identifier}`;
      rulesRaw = target.getAttribute(attribute);
    }

    if (!rulesRaw) return [];

    const cachedRule = this.rulesCache[rulesRaw];
    if (cachedRule) return cachedRule;

    let parsedRules;

    try {
      parsedRules = JSON.parse(rulesRaw);
    } catch (error) {
      this.context.handleError(
        error,
        `Unable to parse rule at the attribute '${attribute}'.`,
      );
      return [];
    }

    const rules = (
      Array.isArray(parsedRules) ? parsedRules : Object.entries(parsedRules)
    )
      .filter(Array.isArray)
      .filter(([key]) => key)
      .map(
        ([fieldName = '', validValues = ''] = []) =>
          [fieldName, castArray(validValues).map(String)] as RuleEntry,
      );

    this.rulesCache[rulesRaw] = rules;

    return rules;
  }

  /* Target disconnection & reconnection */

  enableTargetConnected() {
    this.resolve();
  }

  enableTargetDisconnected() {
    this.resolve();
  }

  showTargetConnected() {
    this.resolve();
  }

  showTargetDisconnected() {
    this.resolve();
  }
}
