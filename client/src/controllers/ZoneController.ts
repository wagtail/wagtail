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
 * @example
 * ```html
 * <div
 *   data-controller="w-zone"
 *   data-w-zone-active-class="hovered active"
 *   data-action="dragover->w-zone#activate dragleave->w-zone#deactivate"
 * >
 *   Drag files here and see the effect.
 * </div>
 * ```
 */
export class ZoneController extends Controller {
  static classes = ['active'];

  static values = {
    delay: { type: Number, default: 0 },
    mode: { type: String, default: ZoneMode.Inactive },
  };

  /** Tracks the current mode for this zone. */
  declare modeValue: ZoneMode;

  /** Classes to append when the mode is active & remove when inactive. */
  declare readonly activeClasses: string[];
  /** Delay, in milliseconds, to use when debouncing the mode updates. */
  declare readonly delayValue: number;

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

  modeValueChanged(current: ZoneMode) {
    const activeClasses = this.activeClasses;

    if (!activeClasses.length) return;

    if (current === ZoneMode.Active) {
      this.element.classList.add(...activeClasses);
    } else {
      this.element.classList.remove(...activeClasses);
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
}
