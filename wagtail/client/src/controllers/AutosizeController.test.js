import { Application } from '@hotwired/stimulus';
import autosize from 'autosize';
import { AutosizeController } from './AutosizeController';

jest.mock('autosize');
jest.useFakeTimers();

describe('AutosizeController', () => {
  let application;
  const resizeObserverMockObserve = jest.fn();
  const resizeObserverMockUnobserve = jest.fn();
  const resizeObserverMockDisconnect = jest.fn();

  const ResizeObserverMock = jest.fn().mockImplementation(() => ({
    observe: resizeObserverMockObserve,
    unobserve: resizeObserverMockUnobserve,
    disconnect: resizeObserverMockDisconnect,
  }));

  global.ResizeObserver = ResizeObserverMock;

  describe('basic behavior', () => {
    beforeAll(() => {
      document.body.innerHTML = `
      <textarea
        data-controller="w-autosize"
        id="text"
      ></textarea>`;
    });

    afterEach(() => {
      jest.clearAllMocks();
    });

    afterAll(() => {
      application.stop();
    });

    it('calls autosize when connected', async () => {
      expect(autosize).not.toHaveBeenCalled();
      expect(ResizeObserverMock).not.toHaveBeenCalled();
      expect(resizeObserverMockObserve).not.toHaveBeenCalled();

      application = Application.start();
      application.register('w-autosize', AutosizeController);

      // await next tick
      await Promise.resolve();

      const textarea = document.getElementById('text');

      expect(autosize).toHaveBeenCalledWith(textarea);
      expect(ResizeObserverMock).toHaveBeenCalledWith(expect.any(Function));
      expect(resizeObserverMockObserve).toHaveBeenCalledWith(textarea);
    });

    it('cleans up on disconnect', async () => {
      expect(autosize.destroy).not.toHaveBeenCalled();
      expect(resizeObserverMockUnobserve).not.toHaveBeenCalled();

      const textarea = document.getElementById('text');

      textarea.remove();

      await Promise.resolve();

      expect(autosize.destroy).toHaveBeenCalledWith(textarea);
      expect(resizeObserverMockDisconnect).toHaveBeenCalled();
    });
  });

  describe('using actions to dispatch methods', () => {
    beforeAll(() => {
      document.body.innerHTML = `
      <textarea
        id="text"
        data-controller="w-autosize"
        data-action="some:event->w-autosize#resize"
      ></textarea>`;

      application = Application.start();
      application.register('w-autosize', AutosizeController);
    });

    afterEach(() => {
      jest.clearAllMocks();
    });

    afterAll(() => {
      application.stop();
    });

    it('calls autosize update from resize method', async () => {
      // await next tick
      await Promise.resolve();

      expect(autosize.update).not.toHaveBeenCalled();

      const textarea = document.getElementById('text');

      textarea.dispatchEvent(new CustomEvent('some:event'));
      jest.runAllTimers(); // resize is debounced

      expect(autosize.update).toHaveBeenCalledWith(textarea);

      // fire multiple events - confirm that the function is debounced

      expect(autosize.update).toHaveBeenCalledTimes(1);
      textarea.dispatchEvent(new CustomEvent('some:event'));
      textarea.dispatchEvent(new CustomEvent('some:event'));
      textarea.dispatchEvent(new CustomEvent('some:event'));
      textarea.dispatchEvent(new CustomEvent('some:event'));
      jest.runAllTimers(); // resize is debounced

      expect(autosize.update).toHaveBeenCalledTimes(2);
    });
  });
});
