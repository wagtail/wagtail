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

    // Attach event listeners to the dialog root (element with id), so it's
    // possible to show/close the dialog somewhere else with no access to the
    // A11yDialog instance.
    templateContent.addEventListener('wagtail:show', () =>
      dialogTemplate.show(),
    );
    templateContent.addEventListener('wagtail:hide', () =>
      dialogTemplate.hide(),
    );
  });
};
