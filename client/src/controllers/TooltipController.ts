import { Controller } from '@hotwired/stimulus';
import tippy, { Placement, Props, Instance, Content } from 'tippy.js';

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
 * ```html
 * <button type="button" data-controller="w-tooltip" data-w-tooltip-content-value="More detail here">
 *   A button with a tooltip
 * </button>
 * ```
 */
export class TooltipController extends Controller<HTMLElement> {
  static values = {
    content: String,
    offset: Array,
    placement: { default: 'bottom', type: String },
  };

  static targets = ['content'];

  declare contentValue: string;
  declare offsetValue: [number, number];
  declare placementValue: Placement;
  declare contentTarget: HTMLElement;

  declare readonly hasOffsetValue: boolean;
  declare readonly hasContentTarget: boolean;

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
    let content: Content = this.contentValue;
    if (this.hasContentTarget) {
      // When using a content target, the HTML is only used once during initialization.
      // We cannot update it later via contentTargetConnected/contentTargetDisconnected,
      // because Tippy immediately unmounts it from the DOM to be remounted later.
      this.contentTarget.hidden = false;
      content = this.contentTarget;
    }

    return {
      content,
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
}
