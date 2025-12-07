/* global ModalWorkflow */
import { domReady } from '../../utils/domReady';
import { encodeForm } from '../../utils/encodeForm';

function openPrivacyModal(url) {
  ModalWorkflow({
    dialogId: 'set-privacy',
    url,
    onload: {
      set_privacy(modal) {
        const form = modal.body.querySelector('form');
        if (!form) return;

        form.addEventListener('submit', (event) => {
          event.preventDefault();

          const action = form.getAttribute('action');
          if (!action) return;

          const body = encodeForm(form);
          modal.postForm(action, body);
        });
      },

      set_privacy_done(modal, { is_public: isPublic }) {
        document.dispatchEvent(
          new CustomEvent('w-privacy:changed', {
            bubbles: true,
            cancelable: false,
            detail: { isPublic },
          }),
        );
        modal.close();
      },
    },
  });
}

function initPrivacySwitch() {
  const buttons = document.querySelectorAll(
    '[data-a11y-dialog-show="set-privacy"]',
  );
  if (!buttons.length) return;

  buttons.forEach((button) => {
    button.addEventListener('click', (event) => {
      event.preventDefault();
      const url = button.getAttribute('data-url');
      openPrivacyModal(url);
    });
  });
}

domReady().then(initPrivacySwitch);
