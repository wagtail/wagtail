import tippy from 'tippy.js';

/**
 Default Tippy Tooltips
 */
export function initTooltips() {
  tippy('[data-tippy-content]');
}

/**
 Actions Dropdown
 <div data-button-with-dropdown>
  <button data-button-with-dropdown-toggle>
  <div data-button-with-dropdown-content>
 </div>
 */

export function initButtonWithModernDropdown() {
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
      });
    }
  });
}
