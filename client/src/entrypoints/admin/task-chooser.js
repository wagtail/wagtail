/* global ModalWorkflow TASK_CHOOSER_MODAL_ONLOAD_HANDLERS */

function createTaskChooser(id) {
  const chooserElement = document.getElementById(`${id}-chooser`);
  if (!chooserElement) return;

  const taskName = chooserElement.querySelector('[data-chooser-title]');
  const input = document.getElementById(id);
  const editAction = chooserElement.querySelector('[data-chooser-edit-link]');
  const chooseButtons = chooserElement.querySelectorAll(
    '[data-chooser-action-choose]',
  );

  chooseButtons.forEach((chooseButton) => {
    chooseButton.addEventListener('click', () => {
      ModalWorkflow({
        url: chooserElement.dataset.chooserUrl,
        onload: TASK_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          taskChosen(data) {
            if (input) {
              input.value = data.id;
            }
            if (taskName) {
              taskName.textContent = data.name;
            }
            chooserElement.classList.remove('blank');
            if (editAction) {
              editAction.setAttribute('href', data.edit_url);
            }
          },
        },
      });
    });
  });
}
window.createTaskChooser = createTaskChooser;
