import { Application } from '@hotwired/stimulus';

import A11yDialog from 'a11y-dialog';
import { DialogController } from './DialogController';

describe('DialogController', () => {
  let application;

  describe('basic behaviour', () => {
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
});
