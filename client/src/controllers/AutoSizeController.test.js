import { Application } from '@hotwired/stimulus';
import autosize from 'autosize';
import { AutoSizeController } from './AutoSizeController';

jest.mock('autosize');

describe('AutoSizeController', () => {
  let application;

  beforeEach(() => {
    application = Application.start();
    application.register('w-auto-size', AutoSizeController);
    document.body.innerHTML = `
    <textarea 
    class="w-field__autosize" 
    data-controller="w-auto-size"
    >
    </textarea>
    `;
  });

  afterEach(() => {
    application.stop();
  });

  it('calls autosize on connect', () => {
    jest.clearAllMocks();
    const textarea = document.querySelector('[data-controller="w-auto-size"]');
    expect(autosize).not.toHaveBeenCalled();
    const controller = application.getControllerForElementAndIdentifier(
      textarea,
      'w-auto-size',
    );
    controller.connect();
    expect(autosize).toHaveBeenCalledWith(textarea);
  });

  it('calls autosize.destroy on disconnect', () => {
    const textarea = document.querySelector('[data-controller="w-auto-size"]');
    const controller = application.getControllerForElementAndIdentifier(
      textarea,
      'w-auto-size',
    );
    controller.connect();
    expect(autosize.destroy).not.toHaveBeenCalled();
    controller.disconnect();
    expect(autosize.destroy).toHaveBeenCalledWith(textarea);
  });

  it('expands the textarea on input', () => {
    const textarea = document.querySelector('.w-field__autosize');
    textarea.value = 'Short text';
    textarea.dispatchEvent(new Event('input'));
    expect(textarea.value).toBe('Short text');
    expect(autosize.update).toHaveBeenCalledWith(textarea);
  });

  it('shrinks the textarea on clearing the value', () => {
    const textarea = document.querySelector('.w-field__autosize');
    application.connectController = (element, controllerName) => {
      const controller = application.getControllerForElementAndIdentifier(
        element,
        controllerName,
      );
      if (controller) {
        controller.connect();
      }
    };
    application.connectController(textarea, 'w-auto-size');
    textarea.value = 'Long text'.repeat(10);
    textarea.dispatchEvent(new Event('input'));
    textarea.value = '';
    textarea.dispatchEvent(new Event('input'));
    expect(autosize.update).toHaveBeenCalledWith(textarea);
    expect(textarea.clientHeight).toBeLessThan(100);
  });
});
