import type { Controller, Definition } from '@hotwired/stimulus';
import { Application } from '@hotwired/stimulus';

/**
 * Wagtail's extension of the base Stimulus `Application` with additional
 * capabilities for convenience.
 */
export class WagtailApplication extends Application {
  /**
   * Returns the first Stimulus controller that matches the identifier.
   * @param identifier - The identifier of the controller to query.
   * @returns The first controller instance that matches the identifier, or null if not found.
   *
   * @example - Querying the PreviewController
   * ```ts
   * const controller = window.wagtail.app.queryController('w-preview');
   * const content = await controller?.extractContent();
   * ```
   */
  queryController<T extends Controller<Element>>(identifier: string) {
    return this.getControllerForElementAndIdentifier(
      document.querySelector(
        `[${this.schema.controllerAttribute}~="${identifier}"]`,
      )!,
      identifier,
    ) as T | null;
  }

  /**
   * Returns all Stimulus controllers that match the identifier.
   * @param identifier - The identifier of the controller to query.
   * @returns An array of controller instances that match the identifier.
   *
   * @example - Querying all instances of the ActionController
   * ```ts
   * const controllers = window.wagtail.app.queryControllerAll('w-action');
   * controllers.forEach((controller) => controller.reset());
   * ```
   */
  queryControllerAll<T extends Controller<Element>>(identifier: string): T[] {
    return Array.from(
      document.querySelectorAll(
        `[${this.schema.controllerAttribute}~="${identifier}"]`,
      ),
    )
      .map((element) =>
        this.getControllerForElementAndIdentifier(element, identifier),
      )
      .filter(Boolean) as T[];
  }
}

/**
 * Initializes the Wagtail Stimulus application, loads the provided controller
 * definitions and returns the app instance.
 *
 * Loads the supplied core controller definitions into the application.
 * Turns on debug mode if in local development.
 */
export const initStimulus = ({
  debug = process.env.NODE_ENV === 'development',
  definitions = [],
  root = document.documentElement,
}: {
  debug?: boolean;
  definitions?: Definition[];
  root?: HTMLElement;
} = {}): WagtailApplication => {
  const app = WagtailApplication.start(root) as WagtailApplication;
  app.debug = debug;
  app.load(definitions);
  return app;
};
