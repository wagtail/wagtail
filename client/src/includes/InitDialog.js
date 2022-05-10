import A11yDialog from 'a11y-dialog';

class Dialog {
  constructor(node) {
    this.dialog = node;
    new A11yDialog(this.dialog);
  }
}

export const initDialog = (
  dialogs = document.querySelectorAll('[data-dialog]'),
) => {
  dialogs.forEach((dialog) => new Dialog(dialog));
};
