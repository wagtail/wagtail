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
    // Dispatch events to hook into behaviour of modals showing / hiding that bubble
    dialogTemplate
      .on('show', (element, event) => {
        html.style.overflowY = 'hidden';
        templateContent.dispatchEvent(
          new CustomEvent('wagtail:dialog-toggle', {
            bubbles: true,
            cancelable: false,
            detail: { event, shown: true },
          }),
        );
      })
      .on('hide', (element, event) => {
        html.style.overflowY = '';
        templateContent.dispatchEvent(
          new CustomEvent('wagtail:dialog-toggle', {
            bubbles: true,
            cancelable: false,
            detail: { event, shown: false },
          }),
        );
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
