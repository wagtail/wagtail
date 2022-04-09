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
const hideTooltipOnBreadcrumbExpand = {
  name: 'hideTooltipOnBreadcrumbExpand',
  fn({ hide }) {
    function onBreadcrumbToggleHover() {
      hide();
    }
    const breadcrumbsToggle = document.querySelector(
      '[data-toggle-breadcrumbs]',
    );

    return {
      onShow() {
        breadcrumbsToggle.addEventListener(
          'mouseenter',
          onBreadcrumbToggleHover,
        );
      },
      onHide() {
        breadcrumbsToggle.removeEventListener(
          'mouseleave',
          onBreadcrumbToggleHover,
        );
      },
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

    if (toggle) {
      content.classList.remove('w-hidden');

      tippy(toggle, {
        content: content,
        trigger: 'click',
        interactive: true,
        theme: 'dropdown',
        placement: 'bottom',
        plugins: [hideTooltipOnEsc, hideTooltipOnBreadcrumbExpand],
      });
    }
  });
}
