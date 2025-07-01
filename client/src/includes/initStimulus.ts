import type { Controller, Definition } from '@hotwired/stimulus';
import { Application } from '@hotwired/stimulus';

class WagtailApplication extends Application {
  queryController(identifier: string): Controller | null {
    return this.getControllerForElementAndIdentifier(
      document.querySelector(
        `[${this.schema.controllerAttribute}="${identifier}"]`,
      )!,
      identifier,
    );
  }

  queryControllerAll(identifier: string): Controller[] {
    return Array.from(
      document.querySelectorAll(
        `[${this.schema.controllerAttribute}="${identifier}"]`,
      ),
    )
      .map((element) =>
        this.getControllerForElementAndIdentifier(element, identifier),
      )
      .filter(Boolean) as Controller[];
  }
}

/**
 * Initialises the Wagtail Stimulus application, loads the provided controller
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
