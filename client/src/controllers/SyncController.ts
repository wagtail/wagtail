import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';

interface SyncControllerEvent extends Event {
  params?: {
    bubbles?: boolean;
    name?: string;
    apply?: string;
  };
}

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
 *     data-w-sync-name-value="image"
 *     data-action="change->w-sync#apply cut->w-sync#clear focus->w-sync#check"
 *     data-w-sync-target-value="#title"
 *   />
 * </section>
 * ```
 *
 * @example - @todo - add an example of using `w-sync` with a file input
 */
export class SyncController extends Controller<HTMLInputElement> {
  static values = {
    debounce: { default: 100, type: Number },
    delay: { default: 0, type: Number },
    disabled: { default: false, type: Boolean },
    name: { default: '', type: String },
    normalize: { default: false, type: Boolean },
    quiet: { default: false, type: Boolean },
    target: String,
  };

  /** The debounce delay in milliseconds, defaults to `100`. */
  declare readonly debounceValue: number;
  /** The delay before applying the value to the target(s), defaults to `0`. */
  declare readonly delayValue: number;
  /** A custom name to use in the event's detail object when dispatching events. */
  declare readonly nameValue: string;
  /** If true, the value will be normalized (e.g. file input will have the extension & fakepath removed) before being applied to the target(s). */
  declare readonly normalizeValue: boolean;
  /** If true, the `change` event will not be dispatched after applying a new value. */
  declare readonly quietValue: boolean;
  /** The target element(s) to sync with, a CSS selector. */
  declare readonly targetValue: string;

  /** If true, the sync controller is disabled and will not apply changes. */
  declare disabledValue: boolean;

  /**
   * Dispatches an event to all target elements so that they can be notified
   * that a sync has started, allowing them to disable the sync by preventing
   * default.
   */
  connect() {
    this.processTargetElements('start', {}, true);
    this.apply = debounce(this.apply.bind(this), this.debounceValue);
  }

  /**
   * Allows for targeted elements to determine, via preventing the default event,
   * whether this sync controller should be disabled.
   */
  check({ params: { bubbles = false } = {} }: SyncControllerEvent) {
    this.processTargetElements('check', { bubbles }, true);
  }

  /**
   * Resolve the controlled element's value that will be used for applying
   * and event dispatching, if configured it will also normalize this value.
   */
  get value() {
    if (!this.normalizeValue) return this.element.value;
    const element = this.element;
    const value = element.value || '';

    switch (element.getAttribute('type')) {
      case 'file':
        // Browser returns the value as `C:\fakepath\image.jpg`,
        // Convert to just the filename part without the extension.
        return (value.split('\\').at(-1) || '').replace(/\.[^.]+$/, '');
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
  apply({ params: { bubbles = false, apply } = {} }: SyncControllerEvent) {
    const applyValue = (target: HTMLInputElement) => {
      /* use setter to correctly update value in non-inputs (e.g. select) */
      target.value = apply || this.value;
      if (this.quietValue) return;
      this.dispatch('change', { cancelable: false, prefix: '', target });
    };

    this.processTargetElements('apply', { bubbles }).forEach((target) => {
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
  clear({ params: { bubbles = false } = {} }: SyncControllerEvent) {
    this.processTargetElements('clear', { bubbles }).forEach((target) => {
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
   *
   * This is the only method that will bubble by default.
   */
  ping({ params: { bubbles = true } = {} }: SyncControllerEvent) {
    this.processTargetElements('ping', { bubbles });
  }

  /**
   * Returns the non-default prevented elements that are targets of this sync
   * controller. Additionally allows this processing to enable or disable
   * this controller instance's sync behavior.
   */
  processTargetElements(
    eventName: string,
    options = {},
    resetDisabledValue = false,
  ) {
    if (!resetDisabledValue && this.disabledValue) return [];

    const name = this.nameValue || '';

    const targetElements = [
      ...document.querySelectorAll<HTMLInputElement>(this.targetValue),
    ];

    const elements = targetElements.filter((target) => {
      const event = this.dispatch(eventName, {
        bubbles: false,
        cancelable: true,
        ...options, // allow overriding some options but not detail & target
        detail: {
          element: this.element,
          ...(name ? { name } : {}), // only include name if set
          value: this.value,
        },
        target: target as HTMLInputElement,
      });

      return !event.defaultPrevented;
    });

    if (resetDisabledValue) {
      this.disabledValue = targetElements.length > elements.length;
    }

    return elements;
  }

  /**
   * Add event listeners to adapt the SyncController `apply` event to the documented
   * `wagtail:images-upload` & `wagtail:documents-upload` events.
   *
   * This intentionally overrides the existing behavior that uses `delay` and `quiet`
   * so that the existing event dispatching is preserved.
   *
   * In a future release we may revisit this and add a deprecation path for this
   * mechanism of event dispatching.
   */
  static afterLoad(identifier: string) {
    const NAMES = ['wagtail:images-upload', 'wagtail:documents-upload'];

    document.addEventListener(
      `${identifier}:apply`,
      (
        event: Event &
          CustomEventInit<{
            element: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
            name: string;
            value: any;
          }>,
      ) => {
        const { detail: { element, name = '', value } = {} } = event;
        const target = event.target as
          | HTMLInputElement
          | HTMLTextAreaElement
          | HTMLSelectElement;

        if (
          !NAMES.includes(name) ||
          !element ||
          !target ||
          !('value' in target)
        ) {
          return;
        }
        const form = element.closest('form');

        // always prevent default on the original event so that we can change the approach
        event.preventDefault();

        if (target.value) return;

        const data = { title: value };

        const adaptedEvent = new CustomEvent(name, {
          bubbles: true,
          cancelable: true,
          detail: {
            data,
            // filename without C:\fakepath\ while preserving the extension
            filename: element.value.split('\\').at(-1),
            maxTitleLength:
              parseInt(target.getAttribute('maxLength') || '0', 10) || null,
          },
        });

        const formEvent = form?.dispatchEvent(adaptedEvent);

        // If a listener has cancelled this event, do not attempt to update the field
        if (!formEvent) return;

        // Update the target (e.g. title field) value with the scoped title
        target.value = data.title;
      },
    );
  }
}
