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
export function initActionsDropdown() {
  const pageEditorActionsDropdown = document.querySelector(
    '[data-page-editor-actions-dropdown]',
  );
  const pageEditorActionsButton = document.querySelector(
    '[data-page-editor-actions-button]',
  );

  pageEditorActionsDropdown.style.display = 'block';

  const tippyDropdown = tippy(pageEditorActionsButton, {
    content: pageEditorActionsDropdown,
    trigger: 'click',
    interactive: true,
    theme: 'dropdown',
    hideOnClick: false, // Only for debugging with dev tools
  });

  tippyDropdown.show();
}
