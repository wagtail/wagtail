/**
 * @jest-environment jsdom
 */

jest.mock('../../utils/domReady', () => ({
  domReady: () => ({
    then(callback) {
      callback();
    },
  }),
}));

describe('admin/privacy-switch entrypoint', () => {
  let trigger;
  let modalOptions;

  beforeEach(() => {
    document.body.innerHTML = `
      <button
        data-a11y-dialog-show="set-privacy"
        data-url="/set-privacy/"
      >
        Set privacy
      </button>
    `;

    window.ModalWorkflow = jest.fn((opts) => {
      modalOptions = opts;
    });

    jest.isolateModules(() => {
      require('./privacy-switch');
    });

    trigger = document.querySelector('[data-a11y-dialog-show="set-privacy"]');
  });

  afterEach(() => {
    modalOptions = undefined;
    document.body.innerHTML = '';
    delete window.ModalWorkflow;
  });

  it('opens ModalWorkflow with expected options on click', () => {
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
    });
    const preventDefaultSpy = jest.spyOn(clickEvent, 'preventDefault');

    trigger.dispatchEvent(clickEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(window.ModalWorkflow).toHaveBeenCalledTimes(1);
    expect(modalOptions.dialogId).toBe('set-privacy');
    expect(modalOptions.url).toBe('/set-privacy/');
    expect(typeof modalOptions.onload.set_privacy).toBe('function');
    expect(typeof modalOptions.onload.set_privacy_done).toBe('function');
  });

  it('wires form submit to modal.postForm in set_privacy', () => {
    const form = document.createElement('form');
    form.setAttribute('action', '/submit/');
    document.body.appendChild(form);

    const modal = {
      body: document.body,
      postForm: jest.fn(),
    };

    trigger.click();
    modalOptions.onload.set_privacy(modal);

    const submitEvent = new Event('submit', {
      bubbles: true,
      cancelable: true,
    });
    const preventDefaultSpy = jest.spyOn(submitEvent, 'preventDefault');

    form.dispatchEvent(submitEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(modal.postForm).toHaveBeenCalledTimes(1);
    expect(modal.postForm).toHaveBeenCalledWith('/submit/', expect.any(String));
  });

  it('does nothing if no form is found in set_privacy', () => {
    const modal = {
      body: document.createElement('div'),
      postForm: jest.fn(),
    };

    trigger.click();
    modalOptions.onload.set_privacy(modal);

    const submitEvent = new Event('submit', {
      bubbles: true,
      cancelable: true,
    });

    modal.body.dispatchEvent(submitEvent);

    expect(modal.postForm).not.toHaveBeenCalled();
  });

  it('dispatches w-privacy:changed and closes the modal in set_privacy_done', () => {
    const close = jest.fn();
    const modal = { close };
    const listener = jest.fn();

    document.addEventListener('w-privacy:changed', listener);

    trigger.click();
    modalOptions.onload.set_privacy_done(modal, { is_public: true });

    expect(listener).toHaveBeenCalledTimes(1);
    const event = listener.mock.calls[0][0];
    expect(event.detail).toEqual({ isPublic: true });

    expect(close).toHaveBeenCalledTimes(1);

    document.removeEventListener('w-privacy:changed', listener);
  });
});
