import $ from 'jquery';

function createTaskChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const taskName = chooserElement.find('[data-chooser-title]');
  const input = $('#' + id);
  const editAction = chooserElement.find('.edit-link');

  $('[data-dialog-show]', chooserElement).on('click', (e) => {
    const dialogId = e.target.getAttribute('data-dialog-show')

    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: chooserElement.data('chooserUrl'),
      dialogId: dialogId,
      // eslint-disable-next-line no-undef
      onload: TASK_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        taskChosen(data) {
          input.val(data.id);
          taskName.text(data.name);
          chooserElement.removeClass('blank');
          editAction.attr('href', data.edit_url);
        },
      },
    });
  });
}
window.createTaskChooser = createTaskChooser;

