import A11yDialog from 'a11y-dialog';

export const initDialog = (
  dialogs = document.querySelectorAll('[data-dialog]'),
) => {
  dialogs.forEach((template) => {
    const html = document.documentElement;
    const templateContent = template.content.firstElementChild.cloneNode(true);
    document.body.appendChild(templateContent);
    const dialog = new A11yDialog(templateContent);

    // Prevent scrolling when dialog is open
    dialog
      .on('show', () => {
        html.style.overflowY = 'hidden';
      })
      .on('hide', () => {
        html.style.overflowY = '';
      });
  });
};
