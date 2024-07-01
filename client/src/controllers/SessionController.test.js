import { Application } from '@hotwired/stimulus';
import { SessionController } from './SessionController';
import { DialogController } from './DialogController';

jest.useFakeTimers();

describe('SessionController', () => {
  let application;

  beforeAll(() => {
    application = Application.start();
    application.register('w-session', SessionController);
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('dispatching ping event at the set interval', () => {
    let handlePing;

    beforeAll(() => {
      handlePing = jest.fn();
      document.addEventListener('w-session:ping', handlePing);
    });

    afterAll(() => {
      document.removeEventListener('w-session:ping', handlePing);
    });

    afterEach(() => {
      handlePing.mockClear();
    });

    it('should dispatch a ping event every 10s by default and can be changed afterwards', async () => {
      expect(handlePing).not.toHaveBeenCalled();
      document.body.innerHTML = /* html */ `
        <div data-controller="w-session">
          Default
        </div>
      `;
      await Promise.resolve();

      // Should dispatch the event immediately
      expect(handlePing).toHaveBeenCalledTimes(1);
      jest.advanceTimersByTime(10000);
      expect(handlePing).toHaveBeenCalledTimes(2);
      jest.advanceTimersByTime(10000);
      expect(handlePing).toHaveBeenCalledTimes(3);
      handlePing.mockClear();
      jest.advanceTimersByTime(123456);
      expect(handlePing).toHaveBeenCalledTimes(12);

      handlePing.mockClear();
      const element = document.querySelector('[data-controller="w-session"]');
      element.setAttribute('data-w-session-interval-value', '20000');
      await Promise.resolve();

      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(1);
      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(2);
      handlePing.mockClear();
      jest.advanceTimersByTime(123456);
      expect(handlePing).toHaveBeenCalledTimes(6);
    });

    it('should allow setting a custom interval value on init and changing it afterwards', async () => {
      expect(handlePing).not.toHaveBeenCalled();
      document.body.innerHTML = /* html */ `
        <div data-controller="w-session" data-w-session-interval-value="5000">
          Custom interval
        </div>
      `;
      await Promise.resolve();

      // Should dispatch the event immediately
      expect(handlePing).toHaveBeenCalledTimes(1);
      jest.advanceTimersByTime(5000);
      expect(handlePing).toHaveBeenCalledTimes(2);
      jest.advanceTimersByTime(5000);
      expect(handlePing).toHaveBeenCalledTimes(3);
      handlePing.mockClear();
      jest.advanceTimersByTime(123456);
      expect(handlePing).toHaveBeenCalledTimes(24);

      handlePing.mockClear();
      const element = document.querySelector('[data-controller="w-session"]');
      element.setAttribute('data-w-session-interval-value', '15000');
      await Promise.resolve();

      jest.advanceTimersByTime(15000);
      expect(handlePing).toHaveBeenCalledTimes(1);
      jest.advanceTimersByTime(15000);
      expect(handlePing).toHaveBeenCalledTimes(2);
      handlePing.mockClear();
      jest.advanceTimersByTime(123456);
      expect(handlePing).toHaveBeenCalledTimes(8);
    });
  });

  describe('dispatching the visibility state of the document', () => {
    let handleHidden;
    let handleVisible;
    let visibility = document.visibilityState;

    beforeAll(() => {
      handleHidden = jest.fn();
      handleVisible = jest.fn();
      document.addEventListener('w-session:hidden', handleHidden);
      document.addEventListener('w-session:visible', handleVisible);

      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        get: () => visibility,
        set: (value) => {
          visibility = value;
          document.dispatchEvent(new Event('visibilitychange'));
        },
      });
    });

    afterAll(() => {
      document.removeEventListener('w-session:hidden', handleHidden);
      document.removeEventListener('w-session:visible', handleVisible);
    });

    afterEach(() => {
      handleHidden.mockClear();
      handleVisible.mockClear();
    });

    it('should dispatch the event', async () => {
      document.body.innerHTML = /* html */ `
        <div
          data-controller="w-session"
          data-action="visibilitychange@document->w-session#dispatchVisibilityState"
        >
          Visibility
        </div>
      `;
      await Promise.resolve();

      expect(handleVisible).not.toHaveBeenCalled();
      expect(handleHidden).not.toHaveBeenCalled();

      document.visibilityState = 'hidden';
      expect(handleHidden).toHaveBeenCalledTimes(1);
      expect(handleVisible).not.toHaveBeenCalled();
      handleHidden.mockClear();

      document.visibilityState = 'visible';
      expect(handleVisible).toHaveBeenCalledTimes(1);
      expect(handleHidden).not.toHaveBeenCalled();
    });
  });

  describe('preventing events triggered by submit buttons in the edit form', () => {
    let handleSubmit;
    let handleWorkflowAction;
    let handleDialogShow;
    let handleDialogHidden;
    let handleDialogConfirmed;
    let form;
    let workflowActionButton;

    beforeAll(() => {
      application.register('w-dialog', DialogController);
      handleSubmit = jest.fn().mockImplementation((e) => e.preventDefault());
      handleWorkflowAction = jest.fn();
      handleDialogShow = jest.fn();
      handleDialogHidden = jest.fn();
      handleDialogConfirmed = jest.fn();
    });

    beforeEach(async () => {
      document.body.innerHTML = /* html */ `
        <form data-edit-form>
          <input type="text" name="title" value="Title" />
          <button type="submit">Save draft</button>
          <button type="button" data-workflow-action-name="approve">Approve</button>

          <div
            id="w-overwrite-changes-dialog"
            aria-hidden="true"
            data-controller="w-dialog"
            data-action="w-dialog:hide->w-dialog#hide w-dialog:show->w-dialog#show"
          >
            <div role="document">
              <div id="dialog-body" data-w-dialog-target="body">
                This will overwrite the changes made by Leon S. Kennedy.

                <button id="confirm" type="button" data-action="click->w-dialog#confirm">Continue</button>
                <button id="cancel" type="button" data-action="click->w-dialog#hide">Cancel</button>
              </div>
            </div>
          </div>
        </form>

        <div
          data-controller="w-session"
          data-w-session-w-dialog-outlet="[data-edit-form] [data-controller='w-dialog']#w-overwrite-changes-dialog"
        >
        </div>
      `;
      await Promise.resolve();

      form = document.querySelector('[data-edit-form]');
      workflowActionButton = form.querySelector('[data-workflow-action-name]');
      form.addEventListener('submit', handleSubmit);
      workflowActionButton.addEventListener('click', handleWorkflowAction, {
        capture: true,
      });
      document.addEventListener('w-dialog:shown', handleDialogShow);
      document.addEventListener('w-dialog:hidden', handleDialogHidden);
      document.addEventListener('w-dialog:confirmed', handleDialogConfirmed);
    });

    afterEach(() => {
      jest.clearAllMocks();
      form.removeEventListener('submit', handleSubmit);
      workflowActionButton.removeEventListener('click', handleWorkflowAction, {
        capture: true,
      });
      document.removeEventListener('w-dialog:shown', handleDialogShow);
      document.removeEventListener('w-dialog:hidden', handleDialogHidden);
      document.removeEventListener('w-dialog:confirmed', handleDialogConfirmed);
    });

    it('should show the dialog and prevent the submit event', async () => {
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const submitButton = form.querySelector('button[type="submit"]');
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(handleDialogShow).not.toHaveBeenCalled();

      submitButton.click();

      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
      expect(handleDialogShow).toHaveBeenCalled();
    });

    it('should continue the action after confirming the dialog', async () => {
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const confirmButton = document.getElementById('confirm');
      expect(handleDialogShow).not.toHaveBeenCalled();

      workflowActionButton.click();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(handleDialogShow).toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
      expect(confirmButton.textContent).toEqual('Continue');

      confirmButton.click();

      expect(handleDialogHidden).toHaveBeenCalled();
      expect(handleDialogConfirmed).toHaveBeenCalled();
      expect(handleWorkflowAction).toHaveBeenCalled();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
    });

    it('should allow the action to be cancelled', async () => {
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const cancelButton = document.getElementById('cancel');
      expect(handleDialogShow).not.toHaveBeenCalled();

      workflowActionButton.click();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(handleDialogShow).toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toBeNull();

      cancelButton.click();

      expect(handleDialogHidden).toHaveBeenCalled();
      expect(handleDialogConfirmed).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
    });

    it('should show the dialog again if clicking the action again after the dialog is hidden', async () => {
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const confirmButton = document.getElementById('confirm');
      const cancelButton = document.getElementById('cancel');
      expect(handleDialogShow).not.toHaveBeenCalled();

      // Clicking a workflow action should show the dialog for the first time
      workflowActionButton.click();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(handleDialogShow).toHaveBeenCalledTimes(1);
      expect(dialog.getAttribute('aria-hidden')).toBeNull();

      confirmButton.click();

      // Confirming the dialog would hide it and continue the action
      expect(handleDialogHidden).toHaveBeenCalledTimes(1);
      expect(handleDialogConfirmed).toHaveBeenCalledTimes(1);
      expect(handleWorkflowAction).toHaveBeenCalledTimes(1);
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      // If the action is clicked again, the dialog should show again
      // (this may happen if the action wasn't completed, so the button is clickable again)
      workflowActionButton.click();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).toHaveBeenCalledTimes(1);
      expect(handleDialogShow).toHaveBeenCalledTimes(2);
      expect(dialog.getAttribute('aria-hidden')).toBeNull();

      cancelButton.click();

      // Cancelling the dialog would hide it and not continue the action
      expect(handleDialogHidden).toHaveBeenCalledTimes(2);
      expect(handleDialogConfirmed).toHaveBeenCalledTimes(1);
      expect(handleWorkflowAction).toHaveBeenCalledTimes(1);
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      // If the action is clicked again, the dialog should show again
      workflowActionButton.click();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).toHaveBeenCalledTimes(1);
      expect(handleDialogShow).toHaveBeenCalledTimes(3);
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
    });

    it('should use the action button label as the dialog confirm target label if it has one', async () => {
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const submitButton = form.querySelector('button[type="submit"]');
      const confirmButton = document.getElementById('confirm');
      // Mark the confirm button as DialogController's confirm target
      confirmButton.setAttribute('data-w-dialog-target', 'confirm');

      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      submitButton.click();

      // The confirm button should use the last clicked action button's label
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
      expect(confirmButton.textContent).toEqual('Save draft');

      confirmButton.click();

      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      workflowActionButton.click();
      // The confirm button should be updated to the new action button's label
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
      expect(confirmButton.textContent).toEqual('Approve');
    });
  });
});
