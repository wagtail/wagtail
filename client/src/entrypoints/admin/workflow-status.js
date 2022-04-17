import $ from 'jquery';

$(() => {
  /* Interface to view the workflow status from the explorer / editor */
  // eslint-disable-next-line func-names
  $('button[data-action-workflow-status]').on('click', function () {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: this.getAttribute('data-url'),
    });
    return false;
  });
});
