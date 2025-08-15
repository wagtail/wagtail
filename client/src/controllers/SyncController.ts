import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';

/**
 * Adds ability to sync the value or interactions with one input with one
 * or more targeted other inputs.
 *
 * @example
 * ```html
 * <section>
 *   <input type="text" name="title" id="title" />
 *   <input
 *     type="date"
 *     id="event-date"
 *     name="event-date"
 *     value="2025-07-22"
 *     data-controller="w-sync"
 *     data-w-sync-name-value": "image" data-w-sync-name-value": "document",
 *     data-action="change->w-sync#apply cut->w-sync#clear focus->w-sync#check"
 *     data-w-sync-target-value="#title"
 *   />
 * </section>
 * ```
 */
export class SyncController extends Controller<HTMLInputElement> {
  static values = {
    debounce: { default: 100, type: Number },
    delay: { default: 0, type: Number },
    disabled: { default: false, type: Boolean },
    quiet: { default: false, type: Boolean },
    event: String,
    normalize: { default: true, type: Boolean },
    keepExisting: { default: false, type: Boolean },
    truncate: { default: false, type: Boolean },
    target: String,
    name: { default: '', type: String },
  };

  declare debounceValue: number;
  declare delayValue: number;
  declare disabledValue: boolean;
  /** If true, the `change` event will not be dispatched after applying a new value. */
  declare quietValue: boolean;
  declare readonly eventValue: string;
  declare readonly targetValue: string;
  declare readonly nameValue: string;
  /** If true, the value will be truncated (to the max length on the target input) before being applied to the target(s), when using `apply` */
  declare truncateValue: boolean;
  /** If true, the value will be normalized (e.g. file input will be converted to spaced words) before being applied to the target(s), when using `apply`. */
  declare normalizeValue: boolean;
  /** If true, the target's input.value(s) (user updated value) will be preserved and no update will be attempted when using `apply`. */
  declare keepExistingValue: boolean;

  /**
   * Dispatches an event to all target elements so that they can be notified
   * that a sync has started, allowing them to disable the sync by preventing
   * default.
   */
  connect() {
    this.processTargetElements('start', true);
    this.apply = debounce(this.apply.bind(this), this.debounceValue);

    this.load();
  }

  /**
   * Allows for targeted elements to determine, via preventing the default event,
   * whether this sync controller should be disabled.
   */
  check() {
    this.processTargetElements('check', true);
  }

  get value() {
    const element = this.element;
    const value = element.value || '';

    switch (this.normalizeValue && element?.getAttribute('type')) {
      // example future - we would need to translate these values maybe though.
      // case 'checkbox':
      //   return element.checked ? 'on' : 'off';
      case 'file':
        // Browser returns the value as `C:\fakepath\image.jpg`,
        // convert to just the filename part
        return (element.value.split('\\').at(-1) || '').replace(/\.[^.]+$/, '');
      default:
        return value;
    }
  }

  /**
   * Applies a value from the controlled element to the targeted
   * elements. Calls to this method are debounced based on the
   * controller's `debounceValue`.
   *
   * Applying of the value to the targets can be done with a delay,
   * based on the controller's `delayValue`.
   */
  apply() {
    const keepExisting = this.keepExistingValue;

    const name = this.nameValue || '';
    const valueToApply = this.value;

    const eventName = ['apply', name].filter(Boolean).join(':');

    const applyValue = (target: HTMLInputElement) => {
      // dispatch an event before applying to check if it should be prevented
      if (
        !this.dispatch(['before-apply', name].filter(Boolean).join(':'), {
          bubbles: true,
          cancelable: true,
          // Allow sending of current and future items
          detail: { element: this.element.value, updated: valueToApply },
        }).defaultPrevented
      )
        /* use setter to correctly update value in non-inputs (e.g. select) */ // eslint-disable-next-line no-param-reassign
        target.value = valueToApply;

      if (this.quietValue) return;

      this.dispatch('change', { cancelable: false, prefix: '', target });
    };

    this.processTargetElements(eventName).forEach((target) => {
      if (keepExisting && (target as HTMLInputElement).value) return;
      if (this.delayValue) {
        setTimeout(() => {
          applyValue(target);
        }, this.delayValue);
      } else {
        applyValue(target);
      }
    });
  }

  /**
   * Clears the value of the targeted elements.
   */
  clear() {
    this.processTargetElements('clear').forEach((target) => {
      setTimeout(() => {
        target.setAttribute('value', '');
        if (this.quietValue) return;
        this.dispatch('change', {
          cancelable: false,
          prefix: '',
          target: target as HTMLInputElement,
        });
      }, this.delayValue);
    });
  }

  /**
   * Simple method to dispatch a ping event to the targeted elements.
   */
  ping() {
    this.processTargetElements('ping', false, { bubbles: true });
  }

  /**
   * Returns the non-default prevented elements that are targets of this sync
   * controller. Additionally allows this processing to enable or disable
   * this controller instance's sync behavior.
   */
  processTargetElements(
    eventName: string,
    resetDisabledValue = false,
    options = {},
  ) {
    if (!resetDisabledValue && this.disabledValue) {
      return [];
    }

    const targetElements = [
      ...document.querySelectorAll<HTMLInputElement>(this.targetValue),
    ];

    const elements = targetElements.filter((target) => {
      const event = this.dispatch(eventName, {
        bubbles: false,
        cancelable: true,
        ...options, // allow overriding some options but not detail & target
        detail: { element: this.element, value: this.element.value },
        target: target as HTMLInputElement,
      });

      return !event.defaultPrevented;
    });

    if (resetDisabledValue) {
      this.disabledValue = targetElements.length > elements.length;
    }

    return elements;
  }

  load() {
    const name = this.element.dataset.wSyncNameValue || '';

    this.element.addEventListener(
      `w-sync:before-apply:${name}`,
      (event: Event) => {
        const custom = event as CustomEvent;

        this.dispatch(`wagtail:${name}s-upload`, {
          bubbles: true,
          cancelable: true,
          detail: {
            original: custom.detail.element,
            updated: custom.detail.updated,
            name,
          },
          target: this.element as HTMLInputElement,
        });
      },
    );
  }
}
