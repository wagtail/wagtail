import { Controller } from '@hotwired/stimulus';
import tippy, { Placement, Props, Instance } from 'tippy.js';
import { domReady } from '../utils/domReady';

/**
 * Hides tooltip when escape key is pressed.
 */
export const hideTooltipOnEsc = {
  name: 'hideOnEsc',
  defaultValue: true,
  fn({ hide }: Instance) {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        hide();
      }
    }

    return {
      onShow() {
        document.addEventListener('keydown', onKeyDown);
      },
      onHide() {
        document.removeEventListener('keydown', onKeyDown);
      },
    };
  },
};

/**
 * A Tippy.js tooltip with simple popover content.
 *
 * @example
 * <button type="button" data-controller="w-tooltip" data-w-tooltip-content-value="More detail here">
 *  A button with a tooltip
 * </button>
 */
export class TooltipController extends Controller<HTMLElement> {
  static values = {
    content: String,
    offset: Array,
    placement: { default: 'bottom', type: String },
  };

  declare contentValue: string;
  declare offsetValue: [number, number];
  declare placementValue: Placement;

  declare readonly hasOffsetValue: boolean;

  tippy?: Instance<Props>;

  connect() {
    this.tippy = tippy(this.element, this.options);
  }

  contentValueChanged(newValue: string, oldValue: string) {
    if (!oldValue || oldValue === newValue) return;
    this.tippy?.setProps(this.options);
  }

  placementValueChanged(newValue: string, oldValue: string) {
    if (!oldValue || oldValue === newValue) return;
    this.tippy?.setProps(this.options);
  }

  hide() {
    this.tippy?.hide();
  }

  show() {
    this.tippy?.show();
  }

  get options(): Partial<Props> {
    return {
      content: this.contentValue,
      placement: this.placementValue,
      plugins: this.plugins,
      ...(this.hasOffsetValue && { offset: this.offsetValue }),
    };
  }

  get plugins() {
    return [hideTooltipOnEsc];
  }

  disconnect() {
    this.tippy?.destroy();
  }

  /**
   * Ensure we have backwards compatibility for any data-tippy usage on initial load.
   *
   * @deprecated RemovedInWagtail70
   */
  static afterLoad() {
    domReady().then(() => {
      tippy('[data-tippy-content]', {
        plugins: [hideTooltipOnEsc],
      });
    });
  }
}
