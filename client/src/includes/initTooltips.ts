import tippy, { Instance } from 'tippy.js';

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
 * Hides tooltip when clicking inside.
 */
export const hideTooltipOnClickInside = {
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
