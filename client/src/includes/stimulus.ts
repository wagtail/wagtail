import { Application, Controller } from '@hotwired/stimulus';
import type { ControllerConstructor } from '@hotwired/stimulus';

import { noop } from '../utils/noop';

type ControllerObjectDefinition = Record<string, () => void> & {
  STATIC?: {
    classes?: string[];
    targets?: string[];
    values: typeof Controller.values;
  };
};

/**
 * Function that accepts a plain old object and returns a Stimulus Controller.
 * Useful when ES6 modules with base class being extended not in use
 * or build tool not in use or for just super convenient class creation.
 *
 * Inspired heavily by
 * https://github.com/StackExchange/Stacks/blob/develop/lib/ts/stacks.ts#L68
 *
 * @example
 * createController({
 *   STATIC: { targets = ['container'] }
 *   connect() {
 *     console.log('connected', this.element, this.containerTarget);
 *   }
 * })
 *
 */
export const createController = (
  controllerDefinition: ControllerObjectDefinition = {},
): typeof Controller => {
  class NewController<X extends Element> extends Controller<X> {}

  // set up static values
  Object.entries(controllerDefinition.STATIC || {}).forEach(([key, value]) => {
    NewController[key] = value;
  });

  // set up class methods
  Object.entries(controllerDefinition)
    .filter(([key]) => !['STATIC'].includes(key))
    .map(([key]) => ({
      key,
      property:
        Object.getOwnPropertyDescriptor(controllerDefinition, key) || noop,
    }))
    .forEach(({ key, property }) => {
      Object.defineProperty(NewController.prototype, key, property);
    });

  return NewController;
};

/**
 * Dispatches events and adds event listeners for documented API surface without relying
 * on exposing the application instance or adding more globals.
 *
 * @example - within Wagtail for custom stimulus controllers
 * ```python
 * @hooks.register('insert_global_admin_js')
 * def global_admin_js():
 *     return mark_safe(
 *         """
 * <script type="module">
 * import { Controller } from "https://unpkg.com/@hotwired/stimulus/dist/stimulus.js";
 *
 * class HelloController extends Controller {
 *   static targets = ["name"];
 *
 *   connect() {
 *     console.log("connected");
 *   }
 * }
 *
 * document.addEventListener(
 *   "wagtail:stimulus-ready",
 *   ({ detail: { register } }) => {
 *     register("hello", HelloController);
 *   },
 *   { once: true }
 * );
 * </script>
 *         """
 *     )
 * ```
 */
const setupApplication = (application: Application) => {
  /**
   * Allows for safe controller registration with logging, with more explicit object
   * param for controller & identifier so that additional arguments can be added later
   * if needed.
   */
  const register = (
    identifier?: string,
    controller?: ControllerConstructor,
  ) => {
    if (!controller || !identifier) {
      application.logDebugActivity(
        'registration failed',
        controller ? 'no identifier' : 'no controller',
        { controller, identifier },
      );
      return;
    }
    application.load({ identifier, controllerConstructor: controller });
    application.logDebugActivity('registered', identifier);
  };

  /**
   * Dispatch event for stimulus being initialised.
   * Most code will not be able to listen to this event,
   * setting up for any future fallbacks/provision of application or
   * cancelling/modifying core controllers.
   */
  document.dispatchEvent(new CustomEvent('wagtail:stimulus-init'));

  /**
   * Add event listener to allow any custom code to trigger debug mode easily.
   */
  window.addEventListener('wagtail:stimulus-enable-debug', () => {
    // eslint-disable-next-line no-param-reassign
    application.debug = true;
    application.logDebugActivity('debug enabled', 'logDebugActivity');
  });

  /**
   * Dispatch event as early as possible and for any core JS already loaded.
   */
  document.addEventListener('readystatechange', () =>
    document.dispatchEvent(
      new CustomEvent('wagtail:stimulus-ready', {
        bubbles: true,
        cancelable: false,
        detail: {
          createController,
          order: document.readyState === 'interactive' ? 0 : 2,
          register,
        },
      }),
    ),
  );

  /**
   * Dispatch event for any other JS loaded async.
   */
  document.addEventListener(
    'DOMContentLoaded',
    () =>
      document.dispatchEvent(
        new CustomEvent('wagtail:stimulus-ready', {
          bubbles: true,
          cancelable: false,
          detail: { createController, order: 1, register },
        }),
      ),
    { once: true },
  );

  /**
   * Allow controller to be registered ad-hoc if DOM ready events are not suitable.
   */
  window.addEventListener('wagtail:stimulus-register-controller', (({
    detail: { controller, identifier },
  }: CustomEvent<{
    identifier?: string;
    controller?: ControllerObjectDefinition | ControllerConstructor;
  }>) => {
    register(
      identifier,
      // if provided with an object
      typeof controller === 'function'
        ? controller
        : createController(controller),
    );
  }) as EventListener);
};

/**
 * Initialises the Wagtail Stimulus application and dispatches and registers
 * custom event behaviour.
 *
 * Loads the the supplied core controller definitions into the application.
 * Turns on debug mode if in local development (for now).
 */
export const initStimulus = ({
  debug = process.env.NODE_ENV === 'development',
  definitions = [],
  element = document.documentElement,
} = {}) => {
  const application = Application.start(element);

  application.debug = !!debug;

  setupApplication(application);

  application.load(definitions);

  return application;
};
