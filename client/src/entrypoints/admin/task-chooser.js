/* global ModalWorkflow TASK_CHOOSER_MODAL_ONLOAD_HANDLERS */

import $ from 'jquery';

function createTaskChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const taskName = chooserElement.find('[data-chooser-title]');
  const input = $('#' + id);
  const editAction = chooserElement.find('[data-chooser-edit-link]');

  $('[data-chooser-action-choose]', chooserElement).on('click', () => {
    ModalWorkflow({
      url: chooserElement.data('chooserUrl'),
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
