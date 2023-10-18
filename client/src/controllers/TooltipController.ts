import { Controller } from '@hotwired/stimulus';
import tippy, { Placement, Props, Instance } from 'tippy.js';
import { hideTooltipOnEsc } from '../includes/initTooltips';

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
      plugins: [hideTooltipOnEsc],
      ...(this.hasOffsetValue && { offset: this.offsetValue }),
    };
  }

  disconnect() {
    this.tippy?.destroy();
  }
}
