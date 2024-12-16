/* global ModalWorkflow */

import $ from 'jquery';

$(() => {
  /* Interface to set permissions from the explorer / editor */
  // eslint-disable-next-line func-names
  $('[data-a11y-dialog-show="set-privacy"]').on('click', function () {
    ModalWorkflow({
      dialogId: 'set-privacy',
      url: this.getAttribute('data-url'),
      onload: {
        set_privacy(modal) {
          // eslint-disable-next-line func-names
          $('form', modal.body).on('submit', function () {
            modal.postForm(this.action, $(this).serialize());
            return false;
          });

          const restrictionTypePasswordField = $(
            "input[name='restriction_type'][value='password']",
            modal.body,
          );
          const restrictionTypeGroupsField = $(
            "input[name='restriction_type'][value='groups']",
            modal.body,
          );
          const passwordField = $('[name="password"]', modal.body).parents(
            '[data-field-wrapper]',
          );
          const groupsFields = $('#groups-fields', modal.body);

          function refreshFormFields() {
            if (restrictionTypePasswordField.is(':checked')) {
              passwordField.show();
              groupsFields.hide();
            } else if (restrictionTypeGroupsField.is(':checked')) {
              passwordField.hide();
              groupsFields.show();
            } else {
              passwordField.hide();
              groupsFields.hide();
            }
          }
          refreshFormFields();

          $("input[name='restriction_type']", modal.body).on(
            'change',
            refreshFormFields,
          );
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
