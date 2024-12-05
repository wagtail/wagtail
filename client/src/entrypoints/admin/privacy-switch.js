/* global ModalWorkflow */

import $ from 'jquery';

$(() => {
  /* Interface to set permissions from the explorer / editor */
  $('[data-a11y-dialog-show="set-privacy"]').on('click', function setPrivacy() {
    ModalWorkflow({
      dialogId: 'set-privacy',
      url: this.getAttribute('data-url'),
      onload: {
        set_privacy(modal) {
          $('form', modal.body).on('submit', function handleSubmit() {
            modal.postForm(this.action, $(this).serialize());
            return false;
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
    return false;
  });
});
