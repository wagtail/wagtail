import { Application } from '@hotwired/stimulus';

import A11yDialog from 'a11y-dialog';
import { DialogController } from './DialogController';

describe('DialogController', () => {
  let application;

  describe('basic behavior', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
      <section>
        <div
          id="dialog-container"
          aria-hidden="true"
          data-controller="w-dialog"
          data-action="w-dialog:hide->w-dialog#hide w-dialog:show->w-dialog#show"
        >
          <div role="document">
            <div id="dialog-body" data-w-dialog-target="body">CONTENT</div>
          </div>
        </div>
      </section>`;

      application = new Application();
      application.register('w-dialog', DialogController);
    });

    afterEach(() => {
      document.body.innerHTML = '';
      jest.clearAllMocks();
    });

    it('should instantiate the controlled element with the A11y library', async () => {
      const listener = jest.fn();
      document.addEventListener('w-dialog:ready', listener);

      expect(listener).not.toHaveBeenCalled();
      application.start();

      await Promise.resolve();

      expect(listener).toHaveBeenCalled();
      const { body, dialog } = listener.mock.calls[0][0].detail;

      expect(body).toEqual(document.getElementById('dialog-body'));
      expect(dialog).toBeInstanceOf(A11yDialog);
      expect(dialog.$el).toEqual(document.getElementById('dialog-container'));
    });

    it('should support the ability to show and hide the dialog', async () => {
      const shownListener = jest.fn();
      document.addEventListener('w-dialog:shown', shownListener);

      const hiddenListener = jest.fn();
      document.addEventListener('w-dialog:hidden', hiddenListener);

      application.start();

      await Promise.resolve();

      expect(shownListener).not.toHaveBeenCalled();
      expect(hiddenListener).not.toHaveBeenCalled();

      const dialog = document.getElementById('dialog-container');

      // closed by default
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(document.documentElement.style.overflowY).toBe('');

      // show the dialog manually
      dialog.dispatchEvent(new CustomEvent('w-dialog:show'));

      expect(dialog.getAttribute('aria-hidden')).toEqual(null);
      expect(shownListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            body: document.getElementById('dialog-body'),
            dialog: expect.any(Object),
          }),
        }),
      );
      expect(hiddenListener).not.toHaveBeenCalled();
      // add style to root element on shown by default
      expect(document.documentElement.style.overflowY).toBe('hidden');

      // hide the dialog manually
      dialog.dispatchEvent(new CustomEvent('w-dialog:hide'));

      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(shownListener).toHaveBeenCalledTimes(1);
      expect(hiddenListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            body: document.getElementById('dialog-body'),
            dialog: expect.any(Object),
          }),
        }),
      );
      // reset style on root element when hidden by default
      expect(document.documentElement.style.overflowY).toBe('');
    });

    it('should support the ability to confirm the dialog with an event to indicate the confirmation', async () => {
      const hiddenListener = jest.fn();
      document.addEventListener('w-dialog:hidden', hiddenListener);

      const confirmedListener = jest.fn();
      document.addEventListener('w-dialog:confirmed', confirmedListener);

      // Add a confirm button to the dialog
      const dialogBody = document.getElementById('dialog-body');
      const confirmButton = document.createElement('button');
      confirmButton.type = 'button';
      confirmButton.setAttribute('data-action', 'w-dialog#confirm');
      dialogBody.appendChild(confirmButton);

      application.start();

      await Promise.resolve();

      expect(hiddenListener).not.toHaveBeenCalled();
      expect(confirmedListener).not.toHaveBeenCalled();

      const dialog = document.getElementById('dialog-container');

      // closed by default
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(document.documentElement.style.overflowY).toBe('');

      // show the dialog manually
      dialog.dispatchEvent(new CustomEvent('w-dialog:show'));

      expect(dialog.getAttribute('aria-hidden')).toEqual(null);
      expect(hiddenListener).not.toHaveBeenCalled();
      expect(confirmedListener).not.toHaveBeenCalled();
      // add style to root element on shown by default
      expect(document.documentElement.style.overflowY).toBe('hidden');

      // hide the dialog using the confirm button
      confirmButton.click();

      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      // w-dialog:hide event should still be dispatched
      expect(hiddenListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            body: dialogBody,
            dialog: expect.any(Object),
          }),
        }),
      );
      // reset style on root element when hidden by default
      expect(document.documentElement.style.overflowY).toBe('');

      // w-dialog:confirmed event should be dispatched
      expect(confirmedListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            body: dialogBody,
            dialog: expect.any(Object),
          }),
        }),
      );
    });

    it('should support the ability use a theme to avoid document style change', async () => {
      const dialog = document.getElementById('dialog-container');

      // adding a theme value
      dialog.classList.add('w-dialog--floating');
      dialog.setAttribute('data-w-dialog-theme-value', 'floating');

      application.start();
      await Promise.resolve();

      // closed by default
      expect(document.documentElement.style.overflowY).toBe('');
      expect(dialog.getAttribute('aria-hidden')).toEqual('true');

      const shownListener = jest.fn();
      document.addEventListener('w-dialog:shown', shownListener);

      const hiddenListener = jest.fn();
      document.addEventListener('w-dialog:hidden', hiddenListener);

      dialog.dispatchEvent(new CustomEvent('w-dialog:show'));

      expect(dialog.getAttribute('aria-hidden')).toEqual(null);
      expect(document.documentElement.style.overflowY).toBeFalsy();
      expect(shownListener).toHaveBeenCalled();

      dialog.dispatchEvent(new CustomEvent('w-dialog:hide'));

      expect(dialog.getAttribute('aria-hidden')).toEqual('true');
      expect(document.documentElement.style.overflowY).toBeFalsy();
      expect(hiddenListener).toHaveBeenCalled();
    });
  });

  describe('dispatching events internally via notify targets', () => {
    const eventHandler = jest.fn();

    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
      <section>
        <div
          id="dialog-container"
          aria-hidden="true"
          data-controller="w-dialog"
          data-action="w-dialog:hide->w-dialog#hide w-dialog:show->w-dialog#show"
        >
          <div role="document">
            <div id="dialog-body" data-w-dialog-target="body">
              <h3>Content</h3>
              <div data-w-dialog-target="notify" id="inner-content"></div>
            </div>
          </div>
          <div data-w-dialog-target="notify" id="outer-content"></div>
        </div>
      </section>`;

      const doc = document.getElementById('inner-content');
      doc.addEventListener('w-dialog:shown', eventHandler);
      doc.addEventListener('w-dialog:hidden', eventHandler);
      doc.addEventListener('w-dialog:ready', eventHandler);

      application = new Application();
      application.register('w-dialog', DialogController);

      application.start();
    });

    afterEach(() => {
      document.body.innerHTML = '';
      jest.clearAllMocks();
    });

    it('should dispatch events to notify targets', async () => {
      const dialogContainer = document.getElementById('dialog-container');

      dialogContainer.dispatchEvent(new CustomEvent('w-dialog:show'));

      // twice, because of show and ready
      expect(eventHandler).toHaveBeenCalledTimes(2);
      // checking the first mock function called
      expect(eventHandler.mock.calls[0][0]).toMatchObject({
        type: 'w-dialog:ready',
        bubbles: false,
      });
      // checking the second mock function called
      expect(eventHandler.mock.calls[1][0]).toMatchObject({
        type: 'w-dialog:shown',
        bubbles: false,
      });

      dialogContainer.dispatchEvent(new CustomEvent('w-dialog:hide'));

      // called once again, therefore 3 times
      expect(eventHandler).toHaveBeenCalledTimes(3);
      // checking the third mock function called
      expect(eventHandler.mock.calls[2][0]).toMatchObject({
        type: 'w-dialog:hidden',
        bubbles: false,
      });
    });
  });
});
