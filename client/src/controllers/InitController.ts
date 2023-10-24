import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a controlled element to add or remove classes
 * when ready to be interacted with.
 *
 * @example
 * <div class="keep-me hide-me" data-controller="w-init" data-w-init-remove-class="hide-me" data-w-init-ready-class="loaded">
 *   When the DOM is ready, this div will have the class 'loaded' added and 'hide-me' removed.
 * </div>
 */
export class InitController extends Controller<HTMLElement> {
  static classes = ['ready', 'remove'];

  static values = {
    delay: { default: -1, type: Number },
  };

  declare readonly readyClasses: string[];
  declare readonly removeClasses: string[];

  declare delayValue: number;

  connect() {
    this.ready();
  }

  /**
   * Add the ready classes and remove the remove classes after a delay.
   * By default, the action will be immediate (negative value).
   * Even when immediate, allow for a microtask delay to allow for other
   * controllers to connect, then do any updates do classes/dispatch events.
   */
  ready() {
    const delayValue = this.delayValue;

    debounce(() => true, delayValue < 0 ? null : delayValue)().then(() => {
      this.element.classList.add(...this.readyClasses);
      this.element.classList.remove(...this.removeClasses);
      this.dispatch('ready', { bubbles: true, cancelable: false });
      this.remove();
    });
  }

  /**
   * Allow the controller to remove itself as it's no longer needed when the init has completed.
   */
  remove() {
    const element = this.element;
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
