import {
  addBulkActionListeners,
  rebindBulkActionsEventListeners,
} from '../../includes/bulk-actions';

document.addEventListener('DOMContentLoaded', addBulkActionListeners);

if (window.headerSearch) {
  const termInput = document.querySelector(window.headerSearch.termInput);
  if (termInput) {
    termInput.addEventListener(
      'search-success',
      rebindBulkActionsEventListeners,
    );
  }
}
