import { Application } from '@hotwired/stimulus';
import { ClipboardController } from './ClipboardController';

jest.useFakeTimers();

describe('ClipboardController', () => {
  const handleEvent = jest.fn();

  document.addEventListener('w-clipboard:copy', handleEvent);
  document.addEventListener('w-clipboard:copied', handleEvent);
  document.addEventListener('w-clipboard:error', handleEvent);

  let app;
  const writeText = jest.fn(() => Promise.resolve());

  const setup = async (
    html = `
  <div id="container" data-controller="w-clipboard" data-action="some-event->w-clipboard#copy">
    <input type="text id="content" data-w-clipboard-target="value" value="copy me to the clipboard" />
    <button type="button" data-action="w-clipboard#copy">Copy</button>
  </div>
  `,
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    app = Application.start();
    app.register('w-clipboard', ClipboardController);

    await Promise.resolve();
  };

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('when the clipboard is not available', () => {
    it('should not have the clipboard available', () => {
      expect(window.navigator.clipboard).toBeUndefined();
    });

    it('should send an error event if the copy method is called', async () => {
      await setup();

      expect(handleEvent).not.toHaveBeenCalled();

      document.querySelector('button').click();

      await jest.runAllTimersAsync();

      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({
          type: 'w-clipboard:error',
          detail: { clear: true, type: 'error' },
        }),
      );
    });
  });

  describe('when the clipboard is available', () => {
    beforeAll(() => {
      Object.defineProperty(window.navigator, 'clipboard', {
        writable: true,
        value: { writeText },
      });
    });

    it('should have the clipboard available', () => {
      expect(window.navigator.clipboard).toBeTruthy();
    });

    it('should copy the content from the value target with the copy method', async () => {
      await setup();

      expect(handleEvent).not.toHaveBeenCalled();
      expect(writeText).not.toHaveBeenCalled();

      document.querySelector('button').click();

      expect(handleEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'w-clipboard:copy' }),
      );

      await jest.runAllTimersAsync();

      expect(writeText).toHaveBeenCalledWith('copy me to the clipboard');
      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({
          type: 'w-clipboard:copied',
          detail: { clear: true, type: 'success' },
        }),
      );
    });

    it('should support a way to block the copy method with event listeners', async () => {
      document.addEventListener(
        'w-clipboard:copy',
        (event) => event.preventDefault(),
        { once: true },
      );

      await setup();

      expect(handleEvent).not.toHaveBeenCalled();
      expect(writeText).not.toHaveBeenCalled();

      document.querySelector('button').click();

      expect(handleEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'w-clipboard:copy' }),
      );

      await jest.runAllTimersAsync();

      expect(writeText).not.toHaveBeenCalled();
      expect(handleEvent).toHaveBeenCalledTimes(1);
    });

    it('should support a custom dispatched event with the value to copy', async () => {
      expect(handleEvent).not.toHaveBeenCalled();
      expect(writeText).not.toHaveBeenCalled();

      await setup();

      document.getElementById('container').dispatchEvent(
        new CustomEvent('some-event', {
          detail: { value: 'copy me from the event' },
        }),
      );

      expect(handleEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'w-clipboard:copy' }),
      );

      await jest.runAllTimersAsync();

      expect(writeText).toHaveBeenCalledWith('copy me from the event');
      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({
          type: 'w-clipboard:copied',
          detail: { clear: true, type: 'success' },
        }),
      );
    });

    it('should support a custom action params to provide the value to copy', async () => {
      expect(handleEvent).not.toHaveBeenCalled();
      expect(writeText).not.toHaveBeenCalled();

      await setup(`
      <div id="container" data-controller="w-clipboard">
        <button type="button" data-action="w-clipboard#copy" data-w-clipboard-value-param="Copy me instead!">Copy</button>
      </div>
      `);

      document.querySelector('button').click();

      expect(handleEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'w-clipboard:copy' }),
      );

      await jest.runAllTimersAsync();

      expect(writeText).toHaveBeenCalledWith('Copy me instead!');
      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({
          type: 'w-clipboard:copied',
          detail: { clear: true, type: 'success' },
        }),
      );
    });

    it('should support falling back to the controlled element value if no other value is provided', async () => {
      expect(handleEvent).not.toHaveBeenCalled();
      expect(writeText).not.toHaveBeenCalled();

      await setup(`
      <textarea id="container" data-controller="w-clipboard" data-action="custom-event->w-clipboard#copy">
        Copy the content inside the controlled element.
      </textarea>
      `);

      document
        .querySelector('textarea')
        .dispatchEvent(new CustomEvent('custom-event'));

      expect(handleEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'w-clipboard:copy' }),
      );

      await jest.runAllTimersAsync();

      expect(writeText).toHaveBeenCalledWith(
        expect.stringContaining(
          'Copy the content inside the controlled element.',
        ),
      );

      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({
          type: 'w-clipboard:copied',
          detail: { clear: true, type: 'success' },
        }),
      );
    });
  });
});
