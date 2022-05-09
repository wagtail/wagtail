import A11yDialog from 'a11y-dialog';
import Tabs from './tabs';

class Dialog {
  constructor(node) {
    this.dialog = node;
  }
}

export const initDialog = (
  dialog = document.querySelectorAll('[data-dialog]'),
) => {
  dialog.forEach((tabSet) => new Dialog(tabSet));
};
