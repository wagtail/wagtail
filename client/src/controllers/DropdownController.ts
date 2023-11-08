import { Controller } from '@hotwired/stimulus';
import tippy, { Content, Props, Instance } from 'tippy.js';
import {
  hideTooltipOnBreadcrumbExpandAndCollapse,
  hideTooltipOnClickInside,
  hideTooltipOnEsc,
  rotateToggleIcon,
} from '../includes/initTooltips';

/**
 * A Tippy.js tooltip with interactive "dropdown" options.
 *
 * @example
 * <div data-controller="w-dropdown" data-w-dropdown-hide-on-click-value-"true">
 *  <button type="button" data-w-dropdown-target="toggle" aria-label="Actions"></button>
 *  <div data-w-dropdown-target="content">[…]</div>
 * </div>
 */
export class DropdownController extends Controller<HTMLElement> {
  static targets = ['toggle', 'content'];
  static values = {
    hideOnClick: { default: false, type: Boolean },
    offset: Array,
  };

  declare hideOnClickValue: boolean;
  declare offsetValue: [number, number];

  declare readonly contentTarget: HTMLDivElement;
  declare readonly hasContentTarget: boolean;
  declare readonly hasOffsetValue: boolean;
  declare readonly toggleTarget: HTMLButtonElement;

  tippy?: Instance<Props>;

  connect() {
    this.tippy = tippy(this.toggleTarget, this.options);
  }

  hide() {
    this.tippy?.hide();
  }

  show() {
    this.tippy?.show();
  }

  /**
   * Default Tippy Options
   */
  get options(): Partial<Props> {
    // If the dropdown toggle uses an ARIA label, use this as a hover tooltip.
    const hoverTooltip = this.toggleTarget.getAttribute('aria-label');
    let hoverTooltipInstance: Instance;

    if (this.hasContentTarget) {
      this.contentTarget.hidden = false;
    }

    if (hoverTooltip) {
      hoverTooltipInstance = tippy(this.toggleTarget, {
        content: hoverTooltip,
        placement: 'bottom',
        plugins: [hideTooltipOnEsc],
      });
    }

    const plugins = [
      hideTooltipOnEsc,
      hideTooltipOnBreadcrumbExpandAndCollapse,
      rotateToggleIcon,
    ];

    if (this.hideOnClickValue) {
      plugins.push(hideTooltipOnClickInside);
    }

    const onShown = () => {
      this.dispatch('shown');
    };

    return {
      ...(this.hasContentTarget
        ? { content: this.contentTarget as Content }
        : {}),
      trigger: 'click',
      interactive: true,
      theme: 'dropdown',
      ...(this.hasOffsetValue && { offset: this.offsetValue }),
      placement: 'bottom',
      plugins,
      onShow() {
        if (hoverTooltipInstance) {
          hoverTooltipInstance.disable();
        }
      },
      onShown() {
        onShown();
      },
      onHide() {
        if (hoverTooltipInstance) {
          hoverTooltipInstance.enable();
        }
      },
    };
  }
}
