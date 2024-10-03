import { Application } from '@hotwired/stimulus';
import { ProgressController } from './ProgressController';

jest.useFakeTimers({ legacyFakeTimers: true });

describe('ProgressController', () => {
  // form submit is not implemented in jsdom
  const mockSubmit = jest.fn((e) => e.preventDefault());
  let application;

  beforeEach(() => {
    document.body.innerHTML = `
    <form id="form">
      <button
        id="button"
        type="submit"
        class="button button-longrunning"
        data-controller="w-progress"
        data-action="w-progress#activate"
        data-w-progress-active-value="Loading"
      >
        <svg>...</svg>
        <em data-w-progress-target="label" id="em-el">Sign in</em>
      </button>
    </form>`;

    document.getElementById('form').addEventListener('submit', mockSubmit);

    application = Application.start();
    application.register('w-progress', ProgressController);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  it('should not change the text of the button to Loading if the form is not valid', () => {
    const form = document.querySelector('form');
    const button = document.querySelector('.button-longrunning');
    expect(mockSubmit).not.toHaveBeenCalled();

    form.noValidate = false;
    form.checkValidity = jest.fn().mockReturnValue(false);
    const onClick = jest.fn();
    button.addEventListener('click', onClick);

    button.dispatchEvent(new CustomEvent('click'));

    expect(setTimeout).not.toHaveBeenCalled();
    expect(button.disabled).toEqual(false);
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('should trigger a timeout based on the value attribute', () => {
    const button = document.querySelector('.button-longrunning');
    jest.spyOn(global, 'setTimeout');

    button.click();

    jest.runAllTimers();

    // default timer 30 seconds
    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 30_000);

    // change to 4 seconds
    document
      .getElementById('button')
      .setAttribute('data-w-progress-duration-value', '4000');

    button.click();
    jest.runAllTimers();

    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 4_000);
  });

  it('should change the text of the button and sets disabled attribute on click', async () => {
    const button = document.querySelector('.button-longrunning');
    const label = document.querySelector('#em-el');
    expect(mockSubmit).not.toHaveBeenCalled();

    button.click();
    jest.advanceTimersByTime(10);
    await new Promise(queueMicrotask);

    expect(label.textContent).toBe('Loading');
    expect(button.getAttribute('disabled')).toEqual('');
    expect(button.classList.contains('button-longrunning-active')).toBe(true);

    jest.runAllTimers();
    await new Promise(queueMicrotask);

    expect(mockSubmit).toHaveBeenCalled();
    expect(label.textContent).toBe('Sign in');
    expect(button.getAttribute('disabled')).toBeNull();
    expect(button.classList.contains('button-longrunning-active')).toBe(false);
  });

  it('should return to the original state when deactivate is called', async () => {
    const button = document.querySelector('.button-longrunning');
    const label = document.querySelector('#em-el');
    const controller = application.getControllerForElementAndIdentifier(
      button,
      'w-progress',
    );

    const setTimeoutSpy = jest.spyOn(global, 'setTimeout');

    button.click();
    jest.advanceTimersByTime(10);
    await new Promise(queueMicrotask);

    expect(label.textContent).toBe('Loading');
    expect(button.getAttribute('disabled')).toEqual('');
    expect(button.classList.contains('button-longrunning-active')).toBe(true);
    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 30_000);

    controller.deactivate();
    await new Promise(queueMicrotask);
    expect(label.textContent).toBe('Sign in');
    expect(button.getAttribute('disabled')).toBeNull();
    expect(button.classList.contains('button-longrunning-active')).toBe(false);

    // Should clear the timeout
    expect(clearTimeout).toHaveBeenLastCalledWith(
      setTimeoutSpy.mock.results.at(-1).value,
    );
  });
});
