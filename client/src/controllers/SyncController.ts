import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';

/**
 * Adds ability to sync the value or interactions with one input with one
 * or more targeted other inputs.
 *
 * @example
 * <section>
 *   <input type="text" name="title" id="title" />
 *   <input
 *     type="date"
 *     id="event-date"
 *     name="event-date"
 *     value="2025-07-22"
 *     data-controller="w-sync"
 *     data-action="change->w-sync#apply cut->w-sync#clear focus->w-sync#check"
 *     data-w-sync-target-value="#title"
 *   />
 * </section>
 */
export class SyncController extends Controller<HTMLInputElement> {
  static values = {
    debounce: { default: 100, type: Number },
    delay: { default: 0, type: Number },
    disabled: { default: false, type: Boolean },
    name: { default: '', type: String },
    normalize: { default: false, type: Boolean },
    quiet: { default: false, type: Boolean },
    target: { default: '', type: String },
  };

  /**
   * The delay, in milliseconds, to wait before running apply if called multiple
   * times consecutively.
   */
  declare debounceValue: number;
  /**
   * The delay, in milliseconds, to wait before applying the value to the target elements.
   */
  declare delayValue: number;
  /**
   * If true, the sync controller will not apply the value to the target elements.
   * Dynamically set when there are no valid target elements to sync with or when all
   * target elements have the apply event prevented on either the `start` or `check` methods.
   */
  declare disabledValue: boolean;
  /**
   * A name value to support differentiation between events.
   */
  declare nameValue: string;
  /**
   * If true, the value to sync will be normalized.
   * @example If the value is a file path, the normalized value will be the file name.
   */
  declare normalizeValue: boolean;
  /**
   * If true, the value will be set on the target elements without dispatching a change event.
   */
  declare quietValue: boolean;

  declare readonly targetValue: string;

  /**
   * Dispatches an event to all target elements so that they can be notified
   * that a sync has started, allowing them to disable the sync by preventing
   * default.
   */
  connect() {
    this.processTargetElements('start', { resetDisabledValue: true });
    this.apply = debounce(this.apply.bind(this), this.debounceValue);
    console.log('SyncController connected to:', this.element);
  }

  /**
   * Allows for targeted elements to determine, via preventing the default event,
   * whether this sync controller should be disabled.
   */
  check() {
    this.processTargetElements('check', { resetDisabledValue: true });
  }

  /**
   * Applies a value from the controlled element to the targeted
   * elements. Calls to this method are debounced based on the
   * controller's `debounceValue`.
   *
   * Applying of the value to the targets can be done with a delay,
   * based on the controller's `delayValue`.
   */
  apply(event?: Event & { params?: { apply?: string } }) {
    const value = this.prepareValue(event?.params?.apply || this.element.value);
    console.log('apply method called');
    const applyValue = (target) => {
      /* use setter to correctly update value in non-inputs (e.g. select) */ // eslint-disable-next-line no-param-reassign
      target.value = value;

      if (this.quietValue) return;

      this.dispatch('change', {
        cancelable: false,
        prefix: '',
        target,
      });
    };

    this.processTargetElements('apply', { value }).forEach((target) => {
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
    this.processTargetElements('ping');
  }

  prepareValue(value: string) {
    if (!this.normalizeValue) return value;

    if (this.element.type === 'file') {
      return value
        .split('\\')
        .slice(-1)[0]
        .replace(/\.[^.]+$/, '');
    }

    return value;
  }

  /**
   * Returns the non-default prevented elements that are targets of this sync
   * controller. Additionally allows this processing to enable or disable
   * this controller instance's sync behaviour.
   */
  processTargetElements(
    eventName: string,
    { resetDisabledValue = false, value = this.element.value } = {},
  ) {
    console.log('Processing target elements for event:', eventName);
    if (!resetDisabledValue && this.disabledValue) {
      // console.log('Sync is disabled, skipping.');
      return [];
    }

    const targetElements = [
      ...document.querySelectorAll<HTMLElement>(this.targetValue),
    ];
    // console.log('Target elements found:', targetElements);

    const element = this.element;
    const name = this.nameValue;

    const elements = targetElements.filter((target) => {
      const maxLength = Number(target.getAttribute('maxlength')) || null;
      const required = !!target.hasAttribute('required');

      const event = this.dispatch(eventName, {
        bubbles: true, // Ensure this is true
        cancelable: true,
        detail: { element, maxLength, name, required, value },
        target,
      });
      // console.log('Event dispatched:', event);
      // console.log('Event target:', target);

      return !event.defaultPrevented;
    });

    if (resetDisabledValue) {
      this.disabledValue = targetElements.length > elements.length;
    }

    return elements;
  }

  /**
   * Could use afterload or something to add backwards compatibility with documented
   * 'wagtail:images|documents-upload' approach.
   */
  static afterLoad(identifier: string) {
    // console.log('is this working?', { identifier });
    if (identifier !== 'w-sync') return;

    // domReady().then(() => {
    // Why does domReady not work???

    // console.log('is this working?');

    /**
     * Need to think this through.
     * I only really want this on specific fields
     * We could normalize all values but is that bad?
     * Need to consider issues with bubbling actions
     * Maybe... using Ping instead for now?
     */

    const handleEvent = (
      event: CustomEvent<{
        maxLength: number | null;
        name: string;
        value: string;
      }>,
    ) => {
      // console.log('sync apply! before', event);
      const {
        /** Will be the target title field */
        target,
      } = event;
      if (!target || !(target instanceof HTMLInputElement)) return;
      const form = target.closest('form');
      if (!form) return;

      // console.log('sync apply!', event);

      const { maxLength: maxTitleLength, name, value: title } = event.detail;

      if (!name || !title) return;

      const data = { title };

      const filename = target.value;

      const wrapperEvent = form.dispatchEvent(
        new CustomEvent(name, {
          bubbles: true,
          cancelable: true,
          detail: {
            ...event.detail,
            data,
            filename,
            maxTitleLength,
          },
        }),
      );

      if (!wrapperEvent) {
        // Do not set a title if event.preventDefault(); is called by handler

        event.preventDefault();
      }

      if (data.title !== title) {
        // If the title has been modified through another listener, update the title field manually, ignoring the default behaviour
        //  or we just always do this???
        event.preventDefault();
        target.value = data.title;
        // maybe dispatch change event - check what jQuery .val does out of the box & check docs!!
      }
    };

    document.addEventListener('w-sync:apply', handleEvent as EventListener);
    // });
  }
}
