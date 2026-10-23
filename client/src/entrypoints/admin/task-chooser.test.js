import './task-chooser';

describe('createTaskChooser', () => {
  const TASK_CHOOSER_HTML = `
    <div id="test-task-chooser" class="chooser task-chooser blank" data-chooser-url="/admin/workflows/tasks/chooser/">
      <div class="chosen">
        <div class="chooser__title" data-chooser-title id="test-task-title">Old Task Name</div>
        <a href="/admin/workflows/tasks/edit/1/" data-chooser-edit-link>Edit this task</a>
        <button type="button" data-chooser-action-choose>Choose another task</button>
      </div>
      <div class="unchosen">
        <button type="button" data-chooser-action-choose class="button">Choose a task</button>
      </div>
    </div>
    <input type="hidden" name="test-task" id="test-task" value="" />
  `;

  let modalWorkflowMock;

  beforeEach(() => {
    document.body.innerHTML = TASK_CHOOSER_HTML;
    modalWorkflowMock = jest.fn();
    window.ModalWorkflow = modalWorkflowMock;
    window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = { chooser: jest.fn() };
  });

  afterEach(() => {
    delete window.ModalWorkflow;
    delete window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS;
    document.body.innerHTML = '';
  });

  it('does nothing when the chooser element does not exist', () => {
    expect(() => {
      window.createTaskChooser('non-existent-id');
    }).not.toThrow();
  });

  it('opens ModalWorkflow with correct parameters when clicking choose button', () => {
    window.createTaskChooser('test-task');

    const chooseButton = document.querySelector(
      '.unchosen [data-chooser-action-choose]',
    );
    chooseButton.click();

    expect(modalWorkflowMock).toHaveBeenCalledTimes(1);
    expect(modalWorkflowMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/admin/workflows/tasks/chooser/',
        onload: window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: expect.objectContaining({
          taskChosen: expect.any(Function),
        }),
      }),
    );
  });

  it('opens ModalWorkflow when clicking choose another task button', () => {
    window.createTaskChooser('test-task');

    const chooseAnotherButton = document.querySelector(
      '.chosen [data-chooser-action-choose]',
    );
    chooseAnotherButton.click();

    expect(modalWorkflowMock).toHaveBeenCalledTimes(1);
  });

  it('updates input value, title, edit link, and removes blank class on taskChosen', () => {
    window.createTaskChooser('test-task');

    const chooseButton = document.querySelector(
      '.unchosen [data-chooser-action-choose]',
    );
    chooseButton.click();

    const { taskChosen } = modalWorkflowMock.mock.calls[0][0].responses;

    taskChosen({
      id: 42,
      name: 'Approval Task',
      edit_url: '/admin/workflows/tasks/edit/42/',
    });

    const chooserElement = document.getElementById('test-task-chooser');
    const input = document.getElementById('test-task');
    const title = document.getElementById('test-task-title');
    const editLink = chooserElement.querySelector('[data-chooser-edit-link]');

    expect(input.value).toBe('42');
    expect(title.textContent).toBe('Approval Task');
    expect(chooserElement.classList.contains('blank')).toBe(false);
    expect(editLink.getAttribute('href')).toBe(
      '/admin/workflows/tasks/edit/42/',
    );
  });
});
