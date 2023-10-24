import type { Definition } from '@hotwired/stimulus';
import { Application } from '@hotwired/stimulus';

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
} = {}): Application => {
  const app = Application.start(root);
  app.debug = debug;
  app.load(definitions);
  return app;
};
