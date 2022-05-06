import $ from 'jquery';

function createTaskChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const taskName = chooserElement.find('.name');
  const input = $('#' + id);
  const editAction = chooserElement.find('.edit-link');

  $('.action-choose', chooserElement).on('click', () => {
    // eslint-disable-next-line no-undef
    ModalWorkflow({
      url: chooserElement.data('chooserUrl'),
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
