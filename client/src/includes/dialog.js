import A11yDialog from 'a11y-dialog';
import ReactDOM from 'react-dom';
import React from 'react';
import { gettext } from '../utils/gettext';
import Icon from '../components/Icon/Icon';

/* Hook for using the A11yDialogs with a passed in dialog element or from a basic template constructed in the function
 * @param {boolean} isChooser - This will be styled as a chooser instead of a dialog.
 * @param {HTMLElement} element - Optional property to create a chooser with a pre-existing element
 * @returns {A11yDialog}
 */
export const useA11yDialog = (element, isChooser, id) => {
  let templateContent;
  const html = document.documentElement;

  // If no pre-existing dialog element has been passed, then create a blank one
  if (element) {
    templateContent = element.content.firstElementChild;
    const { dialogRootSelector } = templateContent.dataset;
    const dialogRoot =
      (dialogRootSelector && document.querySelector(dialogRootSelector)) ||
      document.body;
    dialogRoot.appendChild(templateContent);
  } else {
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.setAttribute('aria-label', gettext('Close dialog'));
    closeButton.classList.add('w-dialog__close-button');
    closeButton.addEventListener('click', () => {
      templateContent.dispatchEvent(new Event('wagtail:hide'));
    });
    ReactDOM.render(<Icon name="cross" />, closeButton);

    const template = `
        <div aria-hidden="true" id="${id}" aria-labelledby="title-${id}" class="w-dialog ${
      isChooser && 'w-dialog--chooser'
    }">
            <div data-a11y-dialog-hide class="w-dialog__overlay"></div>
            <div class="w-dialog__box"><div class="w-dialog__wrapper"><div class="w-dialog__content" data-dialog-body></div></div></div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', template);

    // get the template content as an HTMLElement
    templateContent = document.querySelector(`#${id}`);
    const dialogBog = templateContent.querySelector('.w-dialog__box');
    dialogBog.appendChild(closeButton);
  }

  const dialogTemplate = new A11yDialog(templateContent);

  if (!dialogTemplate && !templateContent) {
    return;
  }

  // Prevent scrolling when dialog is open and dispatch global show/hide events
  dialogTemplate
    .on('show', () => {
      html.style.overflowY = 'hidden';
      document.body.dispatchEvent(new CustomEvent('wagtail:show-dialog'));
    })
    .on('hide', () => {
      html.style.overflowY = '';
      document.body.dispatchEvent(new CustomEvent('wagtail:hide-dialog'));
    });

  // Attach event listeners to the dialog root (element with id), so it's
  // possible to show/close the dialog somewhere else with no access to the
  // A11yDialog instance.
  templateContent.addEventListener('wagtail:show', () => dialogTemplate.show());
  templateContent.addEventListener('wagtail:hide', () => dialogTemplate.hide());

  // eslint-disable-next-line consistent-return
  return dialogTemplate;
};

export const dialog = (
  dialogs = document.querySelectorAll('[data-dialog]'),
) => {
  dialogs.forEach((template) => {
    useA11yDialog(template);
  });
};
