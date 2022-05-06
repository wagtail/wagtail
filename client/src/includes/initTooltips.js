import tippy from 'tippy.js';

const hideTooltipOnEsc = {
  name: 'hideOnEsc',
  defaultValue: true,
  fn({ hide }) {
    function onKeyDown(e) {
      if (e.key === 'Escape') {
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

/*
 Prevents the tooltip from staying open when the breadcrumbs expand and push the toggle button in the layout
 */
const hideTooltipOnBreadcrumbExpandAndCollapse = {
  name: 'hideTooltipOnBreadcrumbAndCollapse',
  fn({ hide }) {
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

/*
 If the toggle button has a toggle arrow, rotate it when open and closed
 */
const rotateToggleIcon = {
  name: 'rotateToggleIcon',
  fn(instance) {
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
 Default Tippy Tooltips
 */
export function initTooltips() {
  tippy('[data-tippy-content]', {
    plugins: [hideTooltipOnEsc],
  });
}

/**
 Actions Dropdown
 <div data-button-with-dropdown>
 <button data-button-with-dropdown-toggle>
 <div data-button-with-dropdown-content>
 </div>
 */

export function initModernDropdown() {
  const containers = document.querySelectorAll('[data-button-with-dropdown]');

  containers.forEach((container) => {
    const content = container.querySelector(
      '[data-button-with-dropdown-content]',
    );
    const toggle = container.querySelector(
      '[data-button-with-dropdown-toggle]',
    );

    // Adding data-hover-tooltip-content="Tooltip Text" to the toggle element will give you a tooltip on hover as well
    const hoverTooltip = toggle.dataset.hoverTooltipContent;
    let hoverTooltipInstance;

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

      tippy(toggle, {
        content: content,
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
      });
    }
  });
}
