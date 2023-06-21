import { Controller } from '@hotwired/stimulus';
import tippy, { Content, Props, Instance } from 'tippy.js';
import {
  hideTooltipOnBreadcrumbExpandAndCollapse,
  hideTooltipOnEsc,
  rotateToggleIcon,
} from '../includes/initTooltips';

/**
 * A Tippy.js tooltip with interactive "dropdown" options.
 *
 * @example
 * <div data-controller="w-dropdown">
 *  <button type="button" data-w-dropdown-target="toggle" aria-label="Actions"></button>
 *  <div data-w-dropdown-target="content">[…]</div>
 * </div>
 */
export class DropdownController extends Controller<HTMLElement> {
  static targets = ['toggle', 'content'];

  declare readonly toggleTarget: HTMLButtonElement;
  declare readonly contentTarget: HTMLDivElement;

  connect() {
    // If the dropdown toggle uses an ARIA label, use this as a hover tooltip.
    const hoverTooltip = this.toggleTarget.getAttribute('aria-label');
    let hoverTooltipInstance: Instance;

    this.contentTarget.hidden = false;

    if (hoverTooltip) {
      hoverTooltipInstance = tippy(this.toggleTarget, {
        content: hoverTooltip,
        placement: 'bottom',
        plugins: [hideTooltipOnEsc],
      });
    }

    /**
     * Default Tippy Options
     */
    const tippyOptions: Partial<Props> = {
      content: this.contentTarget as Content,
      trigger: 'click',
      interactive: true,
      theme: 'dropdown',
      placement: 'bottom',
      plugins: [
        hideTooltipOnEsc,
        hideTooltipOnBreadcrumbExpandAndCollapse,
        rotateToggleIcon,
      ],
      onShow() {
        if (hoverTooltipInstance) {
          hoverTooltipInstance.disable();
        }
      },
      onShown() {
        document.dispatchEvent(new CustomEvent('w-dropdown:shown'));
      },
      onHide() {
        if (hoverTooltipInstance) {
          hoverTooltipInstance.enable();
        }
      },
    };

    tippy(this.toggleTarget, tippyOptions);
  }
}
