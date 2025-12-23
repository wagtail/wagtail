import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

enum ZoneMode {
  Active = 'active',
  Inactive = '',
}

/**
 * Enables the controlled element to respond to specific user interactions
 * by adding or removing CSS classes dynamically.
 *
 * @example - Shows a hover effect when files are dragged over the element.
 * ```html
 * <div
 *   data-controller="w-zone"
 *   data-w-zone-active-class="hovered active"
 *   data-action="dragover->w-zone#activate dragleave->w-zone#deactivate"
 * >
 *   Drag files here and see the effect.
 * </div>
 * ```
 *
 * @example - Switches the active state of the element based on a key value from the switch event.
 * ```html
 * <div
 *   class="super-indicator"
 *   data-controller="w-zone"
 *   data-action="w-privacy:changed@document->w-zone#switch"
 *   data-w-zone-active-class="public"
 *   data-w-zone-inactive-class="private"
 *   data-w-zone-switch-key-value="isPublic"
 * >
 *  Content
 * </div>
 * ```
 */
export class ZoneController extends Controller {
  static classes = ['active', 'inactive'];

  static values = {
    delay: { type: Number, default: 0 },
    mode: { type: String, default: ZoneMode.Inactive },
    switchKey: { type: String, default: '' },
  };

  /** Tracks the current mode for this zone. */
  declare modeValue: ZoneMode;

  /** Classes to append when the mode is active & remove when inactive. */
  declare readonly activeClasses: string[];
  /** Classes to append when the mode is inactive & remove when active. */
  declare readonly inactiveClasses: string[];

  /** Delay, in milliseconds, to use when debouncing the mode updates. */
  declare readonly delayValue: number;
  /** Key to use when switching the active state via the `switch` method. */
  declare readonly switchKeyValue: string;

  initialize() {
    const delayValue = this.delayValue;
    if (delayValue <= 0) return;
    this.activate = debounce(this.activate.bind(this), delayValue);
    // Double the delay for deactivation to prevent flickering.
    this.deactivate = debounce(this.deactivate.bind(this), delayValue * 2);
  }

  activate() {
    this.modeValue = ZoneMode.Active;
  }

  deactivate() {
    this.modeValue = ZoneMode.Inactive;
  }

  modeValueChanged(current: ZoneMode, previous?: ZoneMode) {
    const element = this.element;
    const activeClasses = this.activeClasses;
    const inactiveClasses = this.inactiveClasses;

    // If there are no classes to toggle, or the mode hasn't changed, do nothing.
    if (
      !(activeClasses.length + inactiveClasses.length) ||
      previous === current
    ) {
      return;
    }

    // If the previous mode has not been defined (via ...mode-value), then
    // when running the initial setup, use existing classes to determine the mode.
    if (previous === undefined) {
      if (
        activeClasses.every((className) =>
          element.classList.contains(className),
        )
      ) {
        this.modeValue = ZoneMode.Active;
        // Allow further execution if `activeClasses` is empty
        if (activeClasses.length !== 0) return;
      }

      if (
        inactiveClasses.every((className) =>
          element.classList.contains(className),
        )
      ) {
        this.modeValue = ZoneMode.Inactive;
        // Prevent further execution because above setter will trigger the callback again.
        return;
      }
    }

    // If the mode has changed, update the classes accordingly.
    if (current === ZoneMode.Active) {
      element.classList.add(...activeClasses);
      element.classList.remove(...inactiveClasses);
    } else {
      element.classList.add(...inactiveClasses);
      element.classList.remove(...activeClasses);
    }
  }

  /**
   * Intentionally does nothing.
   *
   * Useful for attaching data-action to leverage the built in
   * Stimulus options without needing any extra functionality.
   * e.g. preventDefault (`:prevent`) and stopPropagation (`:stop`).
   */
  noop() {}

  /**
   * Switches the active state of the zone, based ont he provided key
   * from the event detail or params.
   * If there is no key provided, it will use the fallback key of 'active'.
   *
   * If the key's value is truthy, it will set the mode to active,
   * otherwise it will set it to inactive.
   *
   * If the key is not found in the event detail or params, it will
   * do nothing.
   *
   */
  switch(
    event?: CustomEvent<{ mode?: ZoneMode }> & {
      params?: { mode: ZoneMode };
    },
  ) {
    const { switchKey, ...data } = {
      switchKey: this.switchKeyValue || ZoneMode.Active,
      ...event?.detail,
      ...event?.params,
    };

    const isNegated = switchKey.startsWith('!');
    const key = isNegated ? switchKey.slice(1) : switchKey;

    if (!key || !(key in data)) return;

    const match = !!data[key];
    const modeValue = match === isNegated ? ZoneMode.Inactive : ZoneMode.Active;
    this.modeValue = modeValue;
  }
}
