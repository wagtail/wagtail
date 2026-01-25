import { Application } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { AutosaveController } from './AutosaveController';

jest.useFakeTimers();

describe('AutosaveController', () => {
  let application;

  const setup = async (inner = '') => {
    document.body.innerHTML = /* html */ `
      <form
        action="/autosave/"
        method="post"
        data-controller="w-autosave w-unsaved"
        data-action="w-unsaved:add->w-autosave#save"
      >
        <input type="text" name="title" value="Autosave title" />
        ${inner}
      </form>
    `;

    application = Application.start();
    application.register('w-autosave', AutosaveController);
    // Not registering w-unsaved to keep the test focused on AutosaveController

    await Promise.resolve();

    return document.querySelector('form');
  };

  const dispatchUnsaved = async (form) => {
    const unsavedEvent = new CustomEvent('w-unsaved:add', { bubbles: true });
    form.dispatchEvent(unsavedEvent);
    return unsavedEvent;
  };

  beforeEach(() => {
    fetch.mockReset();
  });

  afterEach(() => {
    application?.stop();
    application = undefined;
    document.body.innerHTML = '';
    fetch.mockReset();
  });

  it('submits form data via fetch and dispatches success event', async () => {
    const form = await setup();
    fetch.mockResponseSuccessJSON(
      JSON.stringify({ success: true, pk: 123, revision_id: 456 }),
    );

    const saveHandler = jest.fn();
    const errorHandler = jest.fn();

    form.addEventListener('w-autosave:save', saveHandler, { once: true });
    form.addEventListener('w-autosave:error', errorHandler, { once: true });
    const successEvent = new Promise((resolve) => {
      form.addEventListener('w-autosave:success', (event) => resolve(event), {
        once: true,
      });
    });

    const unsavedEvent = await dispatchUnsaved(form);
    // rAF doesn't work with jest fake timers
    // https://github.com/jestjs/jest/issues/5147
    const mockRAF = jest.fn((callback) => callback());
    jest.spyOn(window, 'requestAnimationFrame').mockImplementationOnce(mockRAF);
    await jest.advanceTimersByTimeAsync(500);

    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe('http://localhost/autosave/');
    expect(init.method).toBe('post');
    expect(init.headers[WAGTAIL_CONFIG.CSRF_HEADER_NAME]).toBe(
      WAGTAIL_CONFIG.CSRF_TOKEN,
    );
    expect(init.headers['X-Requested-With']).toBeUndefined();

    const payload = Array.from(init.body.entries());
    expect(payload).toEqual(
      expect.arrayContaining([['title', 'Autosave title']]),
    );

    expect(saveHandler).toHaveBeenCalledTimes(1);
    expect(errorHandler).not.toHaveBeenCalled();

    const { detail: successEventDetail } = await successEvent;

    expect(mockRAF).toHaveBeenCalledTimes(1);
    const { response, trigger } = successEventDetail;
    expect(response).toEqual({
      success: true,
      pk: 123,
      revision_id: 456,
    });
    expect(trigger).toBe(unsavedEvent);
  });

  it('does not submit when save event is prevented', async () => {
    const form = await setup();
    const blockSave = jest.fn((event) => event.preventDefault());
    form.addEventListener('w-autosave:save', blockSave, { once: true });

    await dispatchUnsaved(form);
    await jest.advanceTimersByTimeAsync(500);

    expect(blockSave).toHaveBeenCalledTimes(1);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('dispatches an error event when the server responds with an error payload', async () => {
    const form = await setup();

    fetch.mockResponseBadRequest(
      JSON.stringify({
        success: false,
        error_code: 'validation_error',
        error_message: 'Validation error',
      }),
    );

    const errorEvent = new Promise((resolve) => {
      form.addEventListener('w-autosave:error', (event) => resolve(event), {
        once: true,
      });
    });

    const unsavedEvent = await dispatchUnsaved(form);
    await jest.advanceTimersByTimeAsync(500);

    const { detail: errorEventDetail } = await errorEvent;

    expect(fetch).toHaveBeenCalledTimes(1);
    const { response, error, trigger } = errorEventDetail;
    expect(response).toEqual({
      success: false,
      error_code: 'validation_error',
      error_message: 'Validation error',
    });
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe('Validation error');
    expect(trigger).toBe(unsavedEvent);
  });

  it('dispatches an error event when the server response with an unknown JSON response', async () => {
    const form = await setup();

    fetch.mockResponseSuccessJSON(JSON.stringify({ unexpected: 'value' }));

    const errorEvent = new Promise((resolve) => {
      form.addEventListener('w-autosave:error', (event) => resolve(event), {
        once: true,
      });
    });

    const unsavedEvent = await dispatchUnsaved(form);
    await jest.advanceTimersByTimeAsync(500);

    const { detail: errorEventDetail } = await errorEvent;

    expect(fetch).toHaveBeenCalledTimes(1);
    const { response, error, trigger } = errorEventDetail;
    // Response is defined because JSON parsing succeeded
    expect(response).toEqual({ unexpected: 'value' });
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe('Unknown error');
    expect(trigger).toBe(unsavedEvent);
  });

  it('dispatches an error event when the server response with a non-JSON response', async () => {
    const form = await setup();

    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        json: async () => JSON.parse('Invalid JSON'),
      }),
    );

    const errorEvent = new Promise((resolve) => {
      form.addEventListener('w-autosave:error', (event) => resolve(event), {
        once: true,
      });
    });

    const unsavedEvent = await dispatchUnsaved(form);
    await jest.advanceTimersByTimeAsync(500);

    const { detail: errorEventDetail } = await errorEvent;

    expect(fetch).toHaveBeenCalledTimes(1);
    const { response, error, trigger } = errorEventDetail;
    // Response only defined when JSON parsing succeeds
    expect(response).toBeNull();
    expect(error).toBeInstanceOf(SyntaxError);
    expect(trigger).toBe(unsavedEvent);
  });

  it('dispatches an error event when fetch rejects', async () => {
    const form = await setup();

    fetch.mockResponseCrash();

    const errorEvent = new Promise((resolve) => {
      form.addEventListener('w-autosave:error', (event) => resolve(event), {
        once: true,
      });
    });

    const unsavedEvent = await dispatchUnsaved(form);
    await jest.advanceTimersByTimeAsync(500);

    const { detail: errorEventDetail } = await errorEvent;

    expect(fetch).toHaveBeenCalledTimes(1);
    const { response, error, trigger } = errorEventDetail;
    expect(response).toBeNull();
    expect(error).toEqual({ status: 500, statusText: 'Internal Error' });
    expect(trigger).toBe(unsavedEvent);
  });
});
