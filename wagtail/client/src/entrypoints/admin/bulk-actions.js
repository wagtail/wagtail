import {
  addBulkActionListeners,
  rebindBulkActionsEventListeners,
} from '../../includes/bulk-actions';

document.addEventListener('DOMContentLoaded', addBulkActionListeners);
document.addEventListener('w-swap:success', rebindBulkActionsEventListeners);
