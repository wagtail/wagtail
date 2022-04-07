import tippy from 'tippy.js';

/**
 Tippy Tooltips
 */
export function initTooltips() {
  tippy('[data-tippy-content]');
}

/**
 Actions Dropdown
 */
export function initButtonWithDropdown() {
  const buttonWithDropdownMenu = document.querySelector(
    '[data-button-with-dropdown-menu]',
  );
  const buttonWithDropdownToggle = document.querySelector(
    '[data-button-with-dropdown-toggle]',
  );

  if (buttonWithDropdownToggle && buttonWithDropdownToggle) {
    buttonWithDropdownMenu.style.display = 'block';

    tippy(buttonWithDropdownToggle, {
      content: buttonWithDropdownMenu,
      trigger: 'click',
      interactive: true,
      theme: 'dropdown',
    });
  }
}
