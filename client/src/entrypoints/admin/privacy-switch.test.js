jest.mock('../../utils/domReady', () => ({
  domReady: () => Promise.resolve(),
}));

describe('privacy-switch entrypoint', () => {
  let trigger;
  let modalOptions;

  beforeEach(() => {
    document.body.innerHTML = `
      <button type="button" data-a11y-dialog-show="set-privacy" data-url="/set-privacy/">Set privacy</button>
    `;

    window.ModalWorkflow = jest.fn((opts) => {
      modalOptions = opts;
    });

    jest.spyOn(document, 'addEventListener');
    jest.isolateModules(() => {
      require('./privacy-switch');
    });

    trigger = document.querySelector('[data-a11y-dialog-show="set-privacy"]');
  });

  afterEach(() => {
    document.addEventListener.mock.calls.forEach((args) =>
      document.removeEventListener(...args),
    );
    jest.restoreAllMocks();
    modalOptions = undefined;
    document.body.innerHTML = '';
    delete window.ModalWorkflow;
  });

  it('should open the ModalWorkflow with the expected options on click', () => {
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
    });

    trigger.dispatchEvent(clickEvent);

    expect(window.ModalWorkflow).toHaveBeenCalledTimes(1);
    expect(modalOptions.dialogId).toBe('set-privacy');
    expect(modalOptions.url).toBe('/set-privacy/');
    expect(typeof modalOptions.onload.set_privacy).toBe('function');
    expect(typeof modalOptions.onload.set_privacy_done).toBe('function');
  });

  it('should wire form submit to modal.postForm in set_privacy', () => {
    const form = document.createElement('form');
    form.action = '/submit/';
    form.innerHTML = `
      <input type="radio" name="restriction_type" value="none">
      <input type="radio" name="restriction_type" value="password" checked>
      <input type="password" name="password" value="s3cret">
    `;
    document.body.appendChild(form);
    const modal = { body: document.body, postForm: jest.fn() };

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
    expect(modal.postForm).toHaveBeenCalledWith(
      'http://localhost/submit/',
      'restriction_type=password&password=s3cret',
    );
  });

  it('should dispatch w-privacy:changed and close the modal in set_privacy_done', () => {
    const close = jest.fn();
    const modal = { close };
    const listener = jest.fn();
    document.addEventListener('w-privacy:changed', listener);

    trigger.click();
    modalOptions.onload.set_privacy_done(modal, { is_public: true });

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0][0].detail).toEqual({ isPublic: true });
    expect(close).toHaveBeenCalledTimes(1);
  });

  it('should re-bind triggers when w-autosave:success is dispatched', () => {
    const newTrigger = document.createElement('button');
    newTrigger.type = 'button';
    newTrigger.setAttribute('data-a11y-dialog-show', 'set-privacy');
    newTrigger.setAttribute('data-url', '/new-privacy/');
    document.body.appendChild(newTrigger);

    document.dispatchEvent(new CustomEvent('w-autosave:success'));

    newTrigger.click();

    expect(window.ModalWorkflow).toHaveBeenCalledTimes(1);
    expect(window.ModalWorkflow).toHaveBeenCalledWith(
      expect.objectContaining({
        dialogId: 'set-privacy',
        url: '/new-privacy/',
      }),
    );

    trigger.click();

    expect(window.ModalWorkflow).toHaveBeenCalledTimes(2);
  });
});
