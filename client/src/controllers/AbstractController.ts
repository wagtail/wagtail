import { Controller } from '@hotwired/stimulus';
import type { ControllerConstructor } from '@hotwired/stimulus';

export type AbstractControllerConstructor = ControllerConstructor &
  typeof AbstractController;

/**
 * Core abstract controller to keep any specific logic that is desired and
 * to house generic types as needed.
 */
export abstract class AbstractController<
  T extends Element,
> extends Controller<T> {
  static isIncludedInCore = true;
}
