import A11yDialog from 'a11y-dialog';

export const dialog = (
  dialogs = document.querySelectorAll('[data-dialog]'),
) => {
  dialogs.forEach((template) => {
    const html = document.documentElement;
    const templateContent = template.content.firstElementChild;
    document.body.appendChild(templateContent);
    const dialogTemplate = new A11yDialog(templateContent);

    // Prevent scrolling when dialog is open
    dialogTemplate
      .on('show', () => {
        html.style.overflowY = 'hidden';
      })
      .on('hide', () => {
        html.style.overflowY = '';
      });
  });
};
