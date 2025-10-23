import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a controlled element to dispatch an event and also
 * add or remove classes when ready to be interacted with.
 *
 * @example - Dynamic classes when ready
 * ```html
 * <div class="keep-me hide-me" data-controller="w-init" data-w-init-remove-class="hide-me" data-w-init-ready-class="loaded">
 *   When the DOM is ready, this div will have the class 'loaded' added and 'hide-me' removed.
 * </div>
 * ```
 *
 * @example - Custom event dispatching
 * ```html
 * <div class="keep-me hide-me" data-controller="w-init" data-w-init-event-value="custom:event other-custom:event">
 *   When the DOM is ready, two additional custom events will be dispatched; `custom:event` and `other-custom:event`.
 * </div>
 * ```
 *
 * @example - Detail dispatching
 * ```html
 * <article data-controller="w-init" data-w-init-detail-value='{"status": "success", "message": "Article has entered the room"}'>
 *  When the DOM is ready, the detail with value of a JSON object above will be dispatched.
 * </article>
 * ```
 */
export class InitController extends Controller<HTMLElement> {
  static classes = ['ready', 'remove'];

  static values = {
    delay: { default: -1, type: Number },
    detail: { default: {}, type: Object },
    event: { default: '', type: String },
  };

  /** The delay before applying ready classes and dispatching events. */
  declare delayValue: number;
  /** The detail value to be dispatched with events when the element is ready. */
  declare detailValue: Record<string, unknown>;
  /** The custom events to be dispatched when the element is ready. */
  declare eventValue: string;

  /** The classes to be added when the element is ready. */
  declare readonly readyClasses: string[];
  /** The classes to be removed when the element is ready. */
  declare readonly removeClasses: string[];

  connect() {
    this.ready();
  }

  /**
   * Add the ready classes and remove the remove classes after a delay.
   * By default, the action will be immediate (negative value).
   * Even when immediate, allow for a microtask delay to allow for other
   * controllers to connect, then do any updates do classes/dispatch events.
   * Support the ability to also dispatch custom event names.
   */
  ready() {
    const delayValue = this.delayValue;
    const detail = { ...this.detailValue };

    debounce(() => true, delayValue < 0 ? null : delayValue)().then(() => {
      this.element.classList.add(...this.readyClasses);
      this.element.classList.remove(...this.removeClasses);

      if (
        this.dispatch('ready', {
          bubbles: true,
          cancelable: true,
          detail,
        }).defaultPrevented
      ) {
        return;
      }

      this.eventValue
        .split(' ')
        .filter(Boolean)
        .forEach((name) => {
          this.dispatch(name, {
            bubbles: true,
            cancelable: false,
            detail,
            prefix: '',
          });
        });

      this.remove();
    });
  }

  /**
   * Allow the controller to remove itself as it's no longer needed when the init has completed.
   * Removing the controller reference and all other specific value/classes data attributes.
   */
  remove() {
    const element = this.element;

    (this.constructor as typeof InitController).classes.forEach((key) => {
      element.removeAttribute(`data-${this.identifier}-${key}-class`);
    });

    Object.keys((this.constructor as typeof InitController).values).forEach(
      (key) => {
        element.removeAttribute(`data-${this.identifier}-${key}-value`);
      },
    );

    const controllerAttribute = this.application.schema.controllerAttribute;
    const controllers =
      element.getAttribute(controllerAttribute)?.split(' ') ?? [];
    const newControllers = controllers
      .filter((identifier) => identifier !== this.identifier)
      .join(' ');
    if (newControllers) {
      element.setAttribute(controllerAttribute, newControllers);
    } else {
      element.removeAttribute(controllerAttribute);
    }
  }
}
