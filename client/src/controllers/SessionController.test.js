import { Application } from '@hotwired/stimulus';
import { SessionController } from './SessionController';
import { DialogController } from './DialogController';
import { SwapController } from './SwapController';
import { ActionController } from './ActionController';

jest.useFakeTimers();

describe('SessionController', () => {
  let application;

  beforeAll(() => {
    application = Application.start();
    application.register('w-session', SessionController);
    application.register('w-swap', SwapController);
    application.register('w-action', ActionController);
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

      // Setting it to 0 should stop the interval
      handlePing.mockClear();
      element.setAttribute('data-w-session-interval-value', '0');
      await Promise.resolve();

      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(0);
      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(0);
      handlePing.mockClear();
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

      // Setting it to >= 2**31 should stop the interval
      handlePing.mockClear();
      element.setAttribute('data-w-session-interval-value', `${2 ** 31}`);
      await Promise.resolve();

      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(0);
      jest.advanceTimersByTime(20000);
      expect(handlePing).toHaveBeenCalledTimes(0);
      handlePing.mockClear();
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
          data-w-session-intercept-value="true"
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
      const dialog = document.getElementById('w-overwrite-changes-dialog');
      dialog.addEventListener('w-dialog:shown', handleDialogShow);
      dialog.addEventListener('w-dialog:hidden', handleDialogHidden);
      dialog.addEventListener('w-dialog:confirmed', handleDialogConfirmed);
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

    it('should not prevent the submit event if the intercept value is unset', async () => {
      const submitButton = form.querySelector('button[type="submit"]');
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const element = document.querySelector('[data-controller="w-session"]');
      element.removeAttribute('data-w-session-intercept-value');
      await Promise.resolve();

      submitButton.click();

      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(handleDialogShow).not.toHaveBeenCalled();
    });

    it('should not prevent the submit event if the intercept value is set to false', async () => {
      const submitButton = form.querySelector('button[type="submit"]');
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      const element = document.querySelector('[data-controller="w-session"]');
      element.setAttribute('data-w-session-intercept-value', 'false');
      await Promise.resolve();

      submitButton.click();

      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(handleDialogShow).not.toHaveBeenCalled();
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

    it("should hide the submit button's dialog when it shows the confirmation dialog and show it again afterwards", async () => {
      const confirmButton = document.getElementById('confirm');
      // Mark the confirm button as DialogController's confirm target
      confirmButton.setAttribute('data-w-dialog-target', 'confirm');

      const otherDialog = document.createElement('div');
      otherDialog.id = 'w-schedule-publishing-dialog';
      otherDialog.setAttribute('aria-hidden', 'true');
      otherDialog.setAttribute('data-controller', 'w-dialog');
      otherDialog.setAttribute(
        'data-action',
        'w-dialog:hide->w-dialog#hide w-dialog:show->w-dialog#show',
      );
      otherDialog.innerHTML = /* html */ `
        <div role="document">
          <div id="schedule-publishing-dialog-body" data-w-dialog-target="body">
            Set the publishing schedule

            <input type="datetime-local" name="go_live_at" />
            <input type="datetime-local" name="expire_at" />

            <button type="submit">Save schedule</button>
          </div>
        </div>
      `;

      const otherDialogTrigger = document.createElement('button');
      otherDialogTrigger.type = 'button';
      otherDialogTrigger.setAttribute(
        'data-a11y-dialog-show',
        'w-schedule-publishing-dialog',
      );
      otherDialogTrigger.innerHTML = 'Set schedule';

      form.appendChild(otherDialog);
      form.appendChild(otherDialogTrigger);

      // Reconnect the DialogController so the submit button in the
      // schedule publishing dialog works
      const dialog = document.querySelector('#w-overwrite-changes-dialog');
      dialog.removeAttribute('data-controller');
      await Promise.resolve();
      dialog.setAttribute('data-controller', 'w-dialog');
      await Promise.resolve();

      expect(handleDialogShow).not.toHaveBeenCalled();

      // Show the schedule publishing dialog
      otherDialogTrigger.click();
      expect(otherDialog.getAttribute('aria-hidden')).toBeNull();

      // Should not trigger the confirmation dialog yet
      expect(handleDialogShow).not.toHaveBeenCalled();

      const scheduleSubmitButton = otherDialog.querySelector(
        'button[type="submit"]',
      );
      scheduleSubmitButton.click();
      await Promise.resolve();

      // Should trigger the confirmation dialog
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(handleDialogShow).toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toBeNull();
      expect(confirmButton.textContent).toEqual('Save schedule');

      // Should hide the schedule publishing dialog
      expect(otherDialog.getAttribute('aria-hidden')).toEqual('true');

      // Confirm the dialog
      confirmButton.click();
      await Promise.resolve();

      // Should hide the confirmation dialog and continue the action
      expect(handleDialogHidden).toHaveBeenCalled();
      expect(handleDialogConfirmed).toHaveBeenCalled();
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleWorkflowAction).not.toHaveBeenCalled();
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      // The schedule publishing dialog should still be hidden
      expect(otherDialog.getAttribute('aria-hidden')).toEqual('true');
    });
  });

  describe('storing unsaved changes state to a checkbox input and update reload buttons accordingly', () => {
    let reloadButton;

    beforeEach(() => {
      document.body.innerHTML = /* html */ `
        <form data-controller="w-session" data-action="w-unsaved:add@document->w-session#setUnsavedChanges w-unsaved:clear@document->w-session#setUnsavedChanges">
          <input type="checkbox" name="is_editing" data-w-session-target="unsavedChanges" value="1" />
        </form>
      `;

      reloadButton = document.createElement('button');
      reloadButton.type = 'button';
      reloadButton.setAttribute('data-w-session-target', 'reload');
      reloadButton.setAttribute('data-dialog-id', 'w-unsaved-changes-dialog');
      reloadButton.innerHTML = 'Refresh';
    });

    it('should set the checkbox state to be checked when there is a w-unsaved:add event', async () => {
      const form = document.querySelector('form');
      const checkbox = document.querySelector('input');
      expect(checkbox.checked).toBe(false);

      // when connected, the reload button should be set up to reload the page
      form.appendChild(reloadButton);
      await Promise.resolve();
      expect(reloadButton.getAttribute('data-a11y-dialog-show')).toBeNull();
      expect(reloadButton.getAttribute('data-action')).toEqual(
        'w-action#reload',
      );

      document.dispatchEvent(new CustomEvent('w-unsaved:add'));
      await Promise.resolve();
      expect(checkbox.checked).toBe(true);

      // should be included in the form
      expect(new FormData(form).get('is_editing')).toBe('1');

      // should make the reload button show the unsaved changes dialog instead
      // of reloading, by setting the data-a11y-dialog-show attribute and
      // removing the data-action attribute
      expect(reloadButton.getAttribute('data-a11y-dialog-show')).toEqual(
        'w-unsaved-changes-dialog',
      );
      expect(reloadButton.getAttribute('data-action')).toBeNull();
    });

    it('should set the checkbox state to be unchecked when there is a w-unsaved:clear event', async () => {
      const form = document.querySelector('form');
      const checkbox = document.querySelector('input');
      checkbox.checked = true;
      expect(checkbox.checked).toBe(true);

      // when connected, the reload button should be set up to show the unsaved
      // changes dialog
      form.appendChild(reloadButton);
      await Promise.resolve();
      expect(reloadButton.getAttribute('data-a11y-dialog-show')).toEqual(
        'w-unsaved-changes-dialog',
      );
      expect(reloadButton.getAttribute('data-action')).toBeNull();

      document.dispatchEvent(new CustomEvent('w-unsaved:clear'));
      await Promise.resolve();
      expect(checkbox.checked).toBe(false);

      // should not be included in the form
      expect(new FormData(form).get('is_editing')).toBeNull();

      // should make the reload button reload the page instead of showing the
      // unsaved changes dialog, by setting the data-action attribute and
      // removing the data-a11y-dialog-show attribute
      expect(reloadButton.getAttribute('data-a11y-dialog-show')).toBeNull();
      expect(reloadButton.getAttribute('data-action')).toEqual(
        'w-action#reload',
      );
    });

    it('should work fine if there is no unsavedChanges target', async () => {
      const form = document.querySelector('form');
      const checkbox = document.querySelector('input');
      checkbox.remove();

      document.dispatchEvent(new CustomEvent('w-unsaved:add'));
      await Promise.resolve();
      expect(form.innerHTML.trim()).toEqual('');

      document.dispatchEvent(new CustomEvent('w-unsaved:clear'));
      await Promise.resolve();
      expect(form.innerHTML.trim()).toEqual('');
    });

    it('should work fine if there is no reload target', async () => {
      const form = document.querySelector('form');
      const checkbox = document.querySelector('input');

      // the reloadButton is never appended to the form

      document.dispatchEvent(new CustomEvent('w-unsaved:add'));
      await Promise.resolve();
      expect(form.innerHTML.trim()).toEqual(checkbox.outerHTML.trim());

      document.dispatchEvent(new CustomEvent('w-unsaved:clear'));
      await Promise.resolve();
      expect(form.innerHTML.trim()).toEqual(checkbox.outerHTML.trim());
    });
  });

  describe('updating the session state based on JSON data from an event', () => {
    describe('with complete controller configuration', () => {
      afterEach(() => {
        fetch.mockRestore();
      });

      let element;

      const setup = async () => {
        document.body.innerHTML = /* html */ `
        <form
          method="post"
          data-controller="w-swap w-action w-session"
          data-w-swap-target-value="#w-editing-sessions"
          data-w-swap-json-path-value="html"
          data-w-swap-src-value="http://localhost/sessions/1/"
          data-w-action-url-value="http://localhost/sessions/1/release/"
          data-action="w-session:ping->w-swap#submit w-swap:json->w-session#updateSessionData"
        >
          <div id="w-editing-sessions"></div>
        </form>
      `;
        element = document.querySelector('form');
        await Promise.resolve();
      };

      it('should update the respective controller values', async () => {
        fetch.mockResponseSuccessJSON(
          JSON.stringify({
            html: '',
            ping_url: 'http://localhost/sessions/2/',
            release_url: 'http://localhost/sessions/2/release/',
            other_sessions: [],
          }),
        );
        await setup();

        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost/sessions/1/',
          expect.any(Object),
        );

        // Simulate request finishing
        await Promise.resolve();

        // Simulate JSON parsing
        await Promise.resolve();

        expect(element.dataset.wSwapSrcValue).toEqual(
          'http://localhost/sessions/2/',
        );
        expect(element.dataset.wActionUrlValue).toEqual(
          'http://localhost/sessions/2/release/',
        );

        await Promise.resolve();
        expect(document.getElementById('w-editing-sessions').innerHTML).toEqual(
          '',
        );

        // Simulate ping after 10s
        fetch.mockResponseSuccessJSON(
          JSON.stringify({
            html: '<ul><li>Session 7</li></ul>',
            ping_url: 'http://localhost/sessions/999/',
            release_url: 'http://localhost/sessions/release/999/',
            other_sessions: [{ session_id: 7, revision_id: 456 }],
          }),
        );
        jest.advanceTimersByTime(10000);

        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost/sessions/2/',
          expect.any(Object),
        );

        // Simulate request finishing
        await Promise.resolve();

        // Simulate JSON parsing
        await Promise.resolve();

        expect(element.dataset.wSwapSrcValue).toEqual(
          'http://localhost/sessions/999/',
        );
        expect(element.dataset.wActionUrlValue).toEqual(
          'http://localhost/sessions/release/999/',
        );
        expect(element.dataset.wSessionInterceptValue).toEqual('true');

        await Promise.resolve();
        await Promise.resolve();
        expect(document.getElementById('w-editing-sessions').innerHTML).toEqual(
          '<ul><li>Session 7</li></ul>',
        );
      });

      it('should handle unexpected data gracefully', async () => {
        fetch.mockResponseSuccessJSON(
          JSON.stringify({
            html: '<ul><li>Session 1</li></ul>',
          }),
        );
        await setup();

        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost/sessions/1/',
          expect.any(Object),
        );

        // Simulate request finishing
        await Promise.resolve();

        // Simulate JSON parsing
        await Promise.resolve();

        // Should not update the URL values
        expect(element.dataset.wSwapSrcValue).toEqual(
          'http://localhost/sessions/1/',
        );
        expect(element.dataset.wActionUrlValue).toEqual(
          'http://localhost/sessions/1/release/',
        );

        // Should still update the HTML
        await Promise.resolve();
        expect(document.getElementById('w-editing-sessions').innerHTML).toEqual(
          '<ul><li>Session 1</li></ul>',
        );
      });
    });

    describe('with improper configuration', () => {
      let element;
      beforeEach(async () => {
        document.body.innerHTML = /* html */ `
        <div
          data-controller="w-session"
          data-action="w-swap:json->w-session#updateSessionData"
        >
        </div>
      `;
        element = document.querySelector('[data-controller="w-session"]');
        await Promise.resolve();
      });

      afterEach(() => {
        jest.clearAllMocks();
      });

      it('should handle the data gracefully even if SwapController and ActionController are not present', async () => {
        const mock = jest.spyOn(
          SessionController.prototype,
          'updateSessionData',
        );
        element.dispatchEvent(
          new CustomEvent('w-swap:json', {
            detail: {
              data: {
                html: '<ul><li>Session 2</li></ul>',
                ping_url: 'http://localhost/sessions/999/',
                release_url: 'http://localhost/sessions/release/999/',
              },
            },
          }),
        );

        expect(mock).toHaveBeenCalledTimes(1);
        expect(element.dataset.wSwapSrcValue).toBeUndefined();
        expect(element.dataset.wActionUrlValue).toBeUndefined();
      });

      it('should handle the event gracefully even if it does not contain data', async () => {
        const mock = jest.spyOn(
          SessionController.prototype,
          'updateSessionData',
        );
        element.dispatchEvent(
          new CustomEvent('w-swap:json', { detail: { foo: 'bar' } }),
        );

        expect(mock).toHaveBeenCalledTimes(1);
        expect(element.dataset.wSwapSrcValue).toBeUndefined();
        expect(element.dataset.wActionUrlValue).toBeUndefined();
      });
    });
  });
});
