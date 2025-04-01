import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';
import { noop } from '../utils/noop';

type AddOptions = {
  /** Flag for clearing or stacking messages */
  clear?: boolean;
  /** Content for the message, HTML not supported. */
  text?: string;
  /** Clone template type (found using data-type on template targets).
   * e.g. Message status level based on Django's message types. */
  type?: 'success' | 'error' | 'warning' | string;
};

/**
 * Adds the ability for a controlled element to pick an element from a template
 * and then clone that element, adding it to the container.
 * Additionally, it will allow for clearing all previously added elements.
 *
 * @example - Using with the w-messages identifier
 * ```html
 * <div
 *   data-controller="w-messages"
 *   data-action="w-messages:add@document->w-messages#add"
 *   data-w-messages-added-class="new"
 *   data-w-messages-show-class="appear"
 * >
 *   <ul data-w-messages-target="container"></ul>
 *   <template data-w-messages-target="template">
 *     <li data-message-status="error-or-success"><span></span></li>
 *   </template>
 * </div>
 * ```
 *
 * @example - Using to show a temporary element with auto-clearing
 * ```html
 * <div
 *  data-controller="w-clone"
 *  data-action="readystatechange@document->w-clone#add:once"
 *  data-w-clone-auto-clear-value="5_000"
 * >
 *   <div data-w-clone-target="container"></div>
 *     <template data-w-clone-target="template">
 *       <p>Page has loaded, this will be removed in 5 seconds.</p>
 *     </template>
 *   </div>
 * </div>
 * ```
 */
export class CloneController extends Controller<HTMLElement> {
  static classes = ['added', 'hide', 'show'];
  static targets = ['container', 'template'];
  static values = {
    autoClear: { default: 0, type: Number },
    clearDelay: { default: 0, type: Number },
    showDelay: { default: 0, type: Number },
  };

  /** Classes to set on the controlled element after the first usage of add. */
  declare readonly addedClasses: string[];
  /** Classes to set on the controlled element when clearing content or removed when adding content. */
  declare readonly hideClasses: string[];
  /** Target element that will be used to insert the cloned elements. */
  declare readonly containerTarget: HTMLElement;
  /** Classes to set on the controlled element when adding content or removed when clearing content. */
  declare readonly showClasses: string[];
  declare readonly templateTarget: HTMLTemplateElement;
  declare readonly templateTargets: HTMLTemplateElement[];

  /** Auto clears after adding with the declared duration, in milliseconds. If zero or below, will not be used. */
  declare autoClearValue: number;
  /** Delay, in milliseconds, after adjusting classes before the content should be cleared. */
  declare clearDelayValue: number;
  /** Delay, in milliseconds, before adjusting classes on show. */
  declare showDelayValue: number;

  /** Internal tracking of whether a clearing delay is in progress. */
  isClearing?: boolean;

  /**
   * Adds a new element to the container based on the type argument provided in the event
   * or action params objects. Optionally clearing the container first with support for
   * added custom text inside the added element.
   */
  add(event?: CustomEvent<AddOptions> & { params?: AddOptions }) {
    const {
      clear = false,
      text = '',
      type = null,
    } = { ...event?.detail, ...event?.params };

    this.element.classList.add(...this.addedClasses);

    if (clear) this.clear();

    const content = this.getTemplateContent(type);
    if (!content) return;

    const textElement = content.lastElementChild;

    if (textElement instanceof HTMLElement && text) {
      textElement.textContent = text;
    }

    this.containerTarget.appendChild(content);

    debounce(() => {
      this.element.classList.remove(...this.hideClasses);
      this.element.classList.add(...this.showClasses);
      this.dispatch('added', { cancelable: false });
    }, this.showDelayValue || null /* run immediately if zero */)().then(() => {
      // Once complete, check if we should automatically clear the content after a delay
      const autoClearValue = this.autoClearValue || null;
      if (!autoClearValue) return;
      debounce(() => {
        this.clear();
      }, this.autoClearValue)();
    });
  }

  /**
   * If called with an event (or any truthy argument) reset the classes for show/hide
   * so the this method can be used intentionally via actions allowing clearing after
   * animations have run.
   */
  clear(event?: Event) {
    this.isClearing = false;

    if (!event) {
      this.containerTarget.innerHTML = '';
      return;
    }

    const clearDelayValue = this.clearDelayValue || null;
    const element = this.element;

    this.isClearing = true;
    element.classList.remove(...this.addedClasses);
    element.classList.remove(...this.showClasses);
    element.classList.add(...this.hideClasses);

    debounce(noop, clearDelayValue)().then(() => {
      if (!this?.isClearing) return;
      this.containerTarget.innerHTML = '';
      this.dispatch('cleared', { cancelable: false });
      this.isClearing = false;
    });
  }

  /**
   * If no type provided, return the first template target, otherwise try to find
   * a matching target, finally fall back on the first template target if nothing
   * is found.
   */
  getTemplateContent(type?: string | null): HTMLElement | null {
    const template =
      (type &&
        this.templateTargets.find(({ dataset }) => dataset.type === type)) ||
      this.templateTarget;
    const content = template.content.firstElementChild?.cloneNode(true);
    return content instanceof HTMLElement ? content : null;
  }
}
