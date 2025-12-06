import { domReady } from '../../utils/domReady';
import { encodeForm } from '../../utils/encodeForm';

domReady().then(() => {
  /** Interface to set view restrictions from the explorer / editor */
  function setPrivacy(event) {
    const trigger = event.currentTarget;
    const url = trigger.getAttribute('data-url');

    window.ModalWorkflow({
      dialogId: 'set-privacy',
      url,
      onload: {
        set_privacy(modal) {
          const form = modal.body.querySelector('form');
          form?.addEventListener('submit', (submitEvent) => {
            submitEvent.preventDefault();
            modal.postForm(form.action, encodeForm(form));
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

  function bindPrivacySwitch() {
    const privacyTriggers = document.querySelectorAll(
      '[data-a11y-dialog-show="set-privacy"]',
    );

    privacyTriggers.forEach((trigger) => {
      trigger.addEventListener('click', setPrivacy);
    });
  }

  bindPrivacySwitch();

  // Re-bind after side panel content is refreshed e.g. via autosave
  document.addEventListener('w-autosave:success', () => {
    bindPrivacySwitch();
  });
});
