import A11yDialog from 'a11y-dialog';

export const dialog = (
  dialogTemplates = document.querySelectorAll('[data-wagtail-dialog]'),
  rootElement = document.body,
) => {
  const dialogs = Array.from(dialogTemplates).map((template) => {
    const html = document.documentElement;
    const templateContent = template.content.firstElementChild;

    const { dialogRootSelector, theme } = templateContent.dataset;
    const dialogRoot =
      (dialogRootSelector && rootElement.querySelector(dialogRootSelector)) ||
      rootElement;
    dialogRoot.appendChild(templateContent);

    const dialogTemplate = new A11yDialog(templateContent);

    if (theme !== 'floating') {
      // Prevent scrolling when dialog is open
      dialogTemplate
        .on('show', () => {
          html.style.overflowY = 'hidden';
        })
        .on('hide', () => {
          html.style.overflowY = '';
        });
    }

    // Attach event listeners to the dialog root (element with id), so it's
    // possible to show/close the dialog somewhere else with no access to the
    // A11yDialog instance.
    templateContent.addEventListener('wagtail:show', () =>
      dialogTemplate.show(),
    );
    templateContent.addEventListener('wagtail:hide', () =>
      dialogTemplate.hide(),
    );

    return dialogTemplate;
  });

  return dialogs;
};
