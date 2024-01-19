import { Controller } from '@hotwired/stimulus';
import tippy, { Content, Props, Instance } from 'tippy.js';
import { hideTooltipOnEsc } from './TooltipController';

/**
 * Prevents the tooltip from staying open when the breadcrumbs
 * expand and push the toggle button in the layout.
 */
const hideTooltipOnBreadcrumbsChange = {
  name: 'hideTooltipOnBreadcrumbAndCollapse',
  fn({ hide }: Instance) {
    function onBreadcrumbExpandAndCollapse() {
      hide();
    }

    return {
      onShow() {
        document.addEventListener(
          'w-breadcrumbs:opened',
          onBreadcrumbExpandAndCollapse,
        );
        document.addEventListener(
          'w-breadcrumbs:closed',
          onBreadcrumbExpandAndCollapse,
        );
      },
      onHide() {
        document.removeEventListener(
          'w-breadcrumbs:closed',
          onBreadcrumbExpandAndCollapse,
        );
        document.removeEventListener(
          'w-breadcrumbs:opened',
          onBreadcrumbExpandAndCollapse,
        );
      },
    };
  },
};

/**
 * Hides tooltip when clicking inside.
 */
const hideTooltipOnClickInside = {
  name: 'hideTooltipOnClickInside',
  defaultValue: true,
  fn(instance: Instance) {
    const onClick = () => instance.hide();

    return {
      onShow() {
        instance.popper.addEventListener('click', onClick);
      },
      onHide() {
        instance.popper.removeEventListener('click', onClick);
      },
    };
  },
};

/**
 * If the toggle button has a toggle arrow,
 * rotate it when open and closed.
 */
export const rotateToggleIcon = {
  name: 'rotateToggleIcon',
  fn(instance: Instance) {
    const dropdownIcon = instance.reference.querySelector(
      '.icon-arrow-down, .icon-arrow-up',
    );

    if (!dropdownIcon) {
      return {};
    }

    return {
      onShow: () => dropdownIcon.classList.add('w-rotate-180'),
      onHide: () => dropdownIcon.classList.remove('w-rotate-180'),
    };
  },
};

const themeOptions = {
  'dropdown': {
    arrow: true,
    maxWidth: 350,
    placement: 'bottom',
  },
  'drilldown': {
    arrow: false,
    maxWidth: 'none',
    placement: 'bottom-end',
  },
  'dropdown-button': {
    arrow: false,
    maxWidth: 'none',
    placement: 'bottom-start',
  },
} as const;

type TippyTheme = keyof typeof themeOptions;

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
    theme: { default: 'dropdown' as TippyTheme, type: String },
  };

  declare hideOnClickValue: boolean;
  declare offsetValue: [number, number];

  declare readonly contentTarget: HTMLDivElement;
  declare readonly hasContentTarget: boolean;
  declare readonly hasOffsetValue: boolean;
  declare readonly toggleTarget: HTMLButtonElement;
  declare readonly themeValue: TippyTheme;

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

    const onShown = () => {
      this.dispatch('shown');
    };

    return {
      ...(this.hasContentTarget
        ? { content: this.contentTarget as Content }
        : {}),
      ...themeOptions[this.themeValue],
      trigger: 'click',
      interactive: true,
      ...(this.hasOffsetValue && { offset: this.offsetValue }),
      getReferenceClientRect: () => this.getReference().getBoundingClientRect(),
      theme: this.themeValue,
      plugins: this.plugins,
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

  get plugins() {
    return [
      hideTooltipOnBreadcrumbsChange,
      hideTooltipOnEsc,
      rotateToggleIcon,
    ].concat(this.hideOnClickValue ? [hideTooltipOnClickInside] : []);
  }

  /**
   * Use a different reference element depending on the theme.
   */
  getReference() {
    const toggleParent = this.toggleTarget.parentElement as HTMLElement;
    return this.themeValue === 'dropdown-button'
      ? (toggleParent.parentElement as HTMLElement)
      : toggleParent;
  }
}
