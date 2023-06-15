import tippy, { Content, Props, Instance } from 'tippy.js';

/**
 * Hides tooltip when escape key is pressed
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
 * Prevents the tooltip from staying open when the breadcrumbs expand and push the toggle button in the layout
 */
export const hideTooltipOnBreadcrumbExpandAndCollapse = {
  name: 'hideTooltipOnBreadcrumbAndCollapse',
  fn({ hide }: Instance) {
    function onBreadcrumbExpandAndCollapse() {
      hide();
    }

    return {
      onShow() {
        document.addEventListener(
          'wagtail:breadcrumbs-expand',
          onBreadcrumbExpandAndCollapse,
        );
        document.addEventListener(
          'wagtail:breadcrumbs-collapse',
          onBreadcrumbExpandAndCollapse,
        );
      },
      onHide() {
        document.removeEventListener(
          'wagtail:breadcrumbs-collapse',
          onBreadcrumbExpandAndCollapse,
        );
        document.removeEventListener(
          'wagtail:breadcrumbs-expand',
          onBreadcrumbExpandAndCollapse,
        );
      },
    };
  },
};

/**
 * If the toggle button has a toggle arrow, rotate it when open and closed
 */
export const rotateToggleIcon = {
  name: 'rotateToggleIcon',
  fn(instance: Instance) {
    const dropdownIcon = instance.reference.querySelector('.icon-arrow-down');

    if (!dropdownIcon) {
      return {};
    }

    return {
      onShow: () => dropdownIcon.classList.add('w-rotate-180'),
      onHide: () => dropdownIcon.classList.remove('w-rotate-180'),
    };
  },
};

/**
 * Default Tippy Tooltips
 */
export function initTooltips() {
  tippy('[data-tippy-content]', {
    plugins: [hideTooltipOnEsc],
  });
}

/**
 * Actions Dropdown initialisation using the Tippy library.
 * @example
 * <div data-button-with-dropdown>
 *  <button data-button-with-dropdown-toggle>...</button>
 *  <div data-button-with-dropdown-content></div>
 * </div>
 */
export function initModernDropdown() {
  const containers = document.querySelectorAll('[data-button-with-dropdown]');

  containers.forEach((container) => {
    const content = container.querySelector(
      '[data-button-with-dropdown-content]',
    );
    const toggle: HTMLElement | null = container.querySelector(
      '[data-button-with-dropdown-toggle]',
    );

    // Adding data-hover-tooltip-content="Tooltip Text" to the toggle element will give you a tooltip on hover as well
    const hoverTooltip = toggle?.dataset.hoverTooltipContent;
    let hoverTooltipInstance: Instance;

    if (toggle) {
      if (content) {
        content.classList.remove('w-hidden');
      }

      if (hoverTooltip) {
        hoverTooltipInstance = tippy(toggle, {
          content: hoverTooltip,
          placement: 'bottom',
          plugins: [hideTooltipOnEsc],
        });
      }

      /**
       * Default Tippy Options
       */
      const tippyOptions: Partial<Props> = {
        content: content as Content,
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
        onHide() {
          if (hoverTooltipInstance) {
            hoverTooltipInstance.enable();
          }
        },
      };

      tippy(toggle, tippyOptions);
    }
  });
}
