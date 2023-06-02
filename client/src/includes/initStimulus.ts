import type { Definition } from '@hotwired/stimulus';
import { Application, Controller } from '@hotwired/stimulus';

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
 * https://github.com/StackExchange/Stacks/blob/v1.6.5/lib/ts/stacks.ts#L84
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
const createController = (
  controllerDefinition: ControllerObjectDefinition = {},
): typeof Controller => {
  class NewController<X extends Element> extends Controller<X> {}

  const { STATIC = {}, ...controllerDefinitionWithoutStatic } =
    controllerDefinition;

  // set up static values
  Object.entries(STATIC).forEach(([key, value]) => {
    NewController[key] = value;
  });

  // set up class methods
  Object.assign(NewController.prototype, controllerDefinitionWithoutStatic);

  return NewController;
};

interface WagtailApplication extends Application {
  base: {
    createController: typeof createController;
    Controller: typeof Controller;
  };
}

/**
 * Initialises the Wagtail Stimulus application and dispatches and registers
 * custom event behaviour. Adds convenience access for Controller creation
 * to the application instance created so that these are not included in any
 * custom usage of the original Application class.
 *
 * Loads the supplied core controller definitions into the application.
 * Turns on debug mode if in local development (for now).
 */
export const initStimulus = ({
  debug = process.env.NODE_ENV === 'development',
  definitions = [],
  element = document.documentElement,
}: {
  debug?: boolean;
  definitions?: Definition[];
  element?: HTMLElement;
} = {}): WagtailApplication => {
  const application = Application.start(element) as WagtailApplication;

  application.base = { createController, Controller };
  application.debug = debug;
  application.load(definitions);

  return application;
};
