import { domReady } from '../../utils/domReady';
import { encodeForm } from '../../utils/encodeForm';

/**
 * Initializes the privacy switch functionality.
 * Attaches event listeners to privacy trigger buttons to open the ModalWorkflow.
 */
domReady().then(() => {
  const privacyTriggers = document.querySelectorAll(
    '[data-a11y-dialog-show="set-privacy"]',
  );

  privacyTriggers.forEach((trigger) => {
    trigger.addEventListener('click', () => {
      const url = trigger.getAttribute('data-url');

      window.ModalWorkflow({
        dialogId: 'set-privacy',
        url,
        onload: {
          set_privacy(modal) {
            const form = modal.body.querySelector('form');
            if (form) {
              form.addEventListener('submit', (submitEvent) => {
                submitEvent.preventDefault();
                const actionUrl = form.getAttribute('action') || form.action;
                modal.postForm(actionUrl, encodeForm(form));
              });
            }
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
    });
  });
});
