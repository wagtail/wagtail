import A11yDialog from 'a11y-dialog';

class Dialog {
  constructor(node) {
    this.dialog = node;
    // es-lin
    new A11yDialog(this.dialog);
  }
}

export const initDialog = (
  dialog = document.querySelectorAll('[data-dialog]'),
) => {
  dialog.forEach((tabSet) => new Dialog(tabSet));
};
