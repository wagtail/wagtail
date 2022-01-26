import $ from 'jquery';

$(() => {
  /* Interface to view the workflow status from the explorer / editor */
  // eslint-disable-next-line func-names
  $('button.action-workflow-status').on('click', function () {
    // eslint-disable-next-line no-undef, new-cap
    ModalWorkflow({
      url: this.getAttribute('data-url'),
    });
    return false;
  });
});
