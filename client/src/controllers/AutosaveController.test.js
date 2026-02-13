import { Application } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import {
  AutosaveController,
  HydrationError,
  ClientErrorCode,
} from './AutosaveController';

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
    jest.spyOn(window.history, 'replaceState');
  });

  afterEach(() => {
    application?.stop();
    application = undefined;
    document.body.innerHTML = '';
    fetch.mockReset();
    window.history.replaceState.mockRestore();
  });

  describe('basic behavior', () => {
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
      jest
        .spyOn(window, 'requestAnimationFrame')
        .mockImplementationOnce(mockRAF);
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

    it('allows changing the interval value for the debounce', async () => {
      const form = await setup();
      form.setAttribute('data-w-autosave-interval-value', '1000');
      await Promise.resolve();

      fetch.mockResponseSuccessJSON(
        JSON.stringify({
          success: true,
          pk: 123,
          revision_id: 456,
          url: '/edit/123/',
        }),
      );
      const unsavedEvent = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(700);
      expect(fetch).toHaveBeenCalledTimes(0);
      await jest.advanceTimersByTimeAsync(300);
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('handling response data', () => {
    it('reuses revision_id as the overwrite_revision_id for subsequent saves', async () => {
      const form = await setup();
      expect(form.getAttribute('data-w-autosave-revision-id-value')).toBeNull();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ success: true, pk: 123, revision_id: 456 }),
      );
      const unsavedEvent1 = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);

      expect(fetch).toHaveBeenCalledTimes(1);
      let [, init] = fetch.mock.calls[0];
      let payload = Array.from(init.body.entries());
      expect(payload).toEqual(
        expect.arrayContaining([['title', 'Autosave title']]),
      );
      expect(payload).not.toEqual(
        expect.arrayContaining([['overwrite_revision_id', '456']]),
      );

      expect(form.getAttribute('data-w-autosave-revision-id-value')).toBe(
        '456',
      );

      // Second autosave
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ success: true, pk: 123, revision_id: 456 }),
      );
      const unsavedEvent2 = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);
      expect(fetch).toHaveBeenCalledTimes(2);
      [, init] = fetch.mock.calls[1];
      payload = Array.from(init.body.entries());
      expect(payload).toEqual(
        expect.arrayContaining([['title', 'Autosave title']]),
      );
      expect(payload).toEqual(
        expect.arrayContaining([['overwrite_revision_id', '456']]),
      );
    });

    it('handles field_updates in the response by updating form fields', async () => {
      const form = await setup(/* html */ `
          <input type="hidden" name="child_items-INITIAL_FORMS" value="6" id="id_child_items-INITIAL_FORMS">
        `);

      fetch.mockResponseSuccessJSON(
        JSON.stringify({
          success: true,
          pk: 123,
          revision_id: 456,
          field_updates: {
            'child_items-INITIAL_FORMS': '7',
            // this field does not exist in the form and should be ignored
            'nonexistent-field': '999',
          },
        }),
      );

      const unsavedEvent = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);

      expect(fetch).toHaveBeenCalledTimes(1);
      const childItemsInitialForms = form.querySelector(
        '#id_child_items-INITIAL_FORMS',
      );
      expect(childItemsInitialForms.value).toBe('7');
    });

    it('updates form action and address bar URL if provided in response', async () => {
      const form = await setup();
      expect(form.action).toBe('http://localhost/autosave/');
      fetch.mockResponseSuccessJSON(
        JSON.stringify({
          success: true,
          pk: 123,
          revision_id: 456,
          url: '/edit/123/',
        }),
      );
      const unsavedEvent = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(form.action).toBe('http://localhost/edit/123/');
      expect(window.history.replaceState).toHaveBeenCalledWith(
        null,
        '',
        '/edit/123/',
      );
    });

    it('loads HTML partials into the partials target if provided in response', async () => {
      const form = await setup(/* html */ `
          <div data-w-autosave-target="partials"></div>
        `);
      const partialsTarget = form.querySelector(
        '[data-w-autosave-target="partials"]',
      );
      expect(partialsTarget.innerHTML).toBe('');
      const html = /* html */ `
        <template data-controller="w-teleport" data-w-teleport-target-value="[data-w-breadcrumbs]" data-w-teleport-mode-value="outerHTML">
          <div data-w-breadcrumbs="">
            Updated breadcrumbs
          </div>
        </template>
      `.trim();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({
          success: true,
          pk: 123,
          revision_id: 456,
          html,
        }),
      );
      const unsavedEvent = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(partialsTarget.innerHTML).toBe(html);
    });
  });

  describe('hydrating the view via hydrate_url', () => {
    let form;
    let partialsTarget;
    const successResponse = {
      success: true,
      pk: 123,
      revision_id: 456,
      hydrate_url: '/edit/123/?_w_hydrate_create_view=1',
    };

    beforeEach(async () => {
      form = await setup(/* html */ `
          <div data-w-autosave-target="partials"></div>
        `);
      partialsTarget = form.querySelector(
        '[data-w-autosave-target="partials"]',
      );
      fetch.mockResponseSuccessJSON(JSON.stringify(successResponse));
    });

    it('fetches and injects HTML from hydrate_url into the partials target', async () => {
      expect(partialsTarget.innerHTML).toBe('');

      const hydrateHtml = /* html */ `
        <template data-controller="w-teleport" data-w-teleport-target-value="[data-w-breadcrumbs]" data-w-teleport-mode-value="outerHTML">
          <div data-w-breadcrumbs="">
            Hydrated breadcrumbs
          </div>
        </template>
      `.trim();

      fetch.mockResponseSuccessText(hydrateHtml);

      const unsavedEvent = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(fetch.mock.calls[1][0]).toBe(
        '/edit/123/?_w_hydrate_create_view=1',
      );
      expect(partialsTarget.innerHTML).toBe(hydrateHtml);
    });

    describe('error handling for hydration requests', () => {
      it('dispatches an error event when the fetch fails', async () => {
        expect(partialsTarget.innerHTML).toBe('');

        fetch.mockResponseCrash();

        const errorEvent = new Promise((resolve) => {
          form.addEventListener('w-autosave:error', (event) => resolve(event), {
            once: true,
          });
        });

        const unsavedEvent = await dispatchUnsaved(form);
        await jest.advanceTimersByTimeAsync(500);

        expect(fetch).toHaveBeenCalledTimes(2);
        expect(fetch.mock.calls[1][0]).toBe(
          '/edit/123/?_w_hydrate_create_view=1',
        );

        const { detail: errorEventDetail } = await errorEvent;

        const { response, error, trigger, text } = errorEventDetail;
        expect(response).toEqual(successResponse);
        expect(error).toBeInstanceOf(HydrationError);
        expect(error.code).toBe(ClientErrorCode.NETWORK_ERROR);
        expect(trigger).toBe(unsavedEvent);
        expect(text).toBe('A network error occurred.');
      });

      it('dispatches an error event when the server responds with an error', async () => {
        expect(partialsTarget.innerHTML).toBe('');

        fetch.mockResponseFailure();

        const errorEvent = new Promise((resolve) => {
          form.addEventListener('w-autosave:error', (event) => resolve(event), {
            once: true,
          });
        });

        const unsavedEvent = await dispatchUnsaved(form);
        await jest.advanceTimersByTimeAsync(500);

        expect(fetch).toHaveBeenCalledTimes(2);
        expect(fetch.mock.calls[1][0]).toBe(
          '/edit/123/?_w_hydrate_create_view=1',
        );

        const { detail: errorEventDetail } = await errorEvent;

        const { response, error, trigger, text } = errorEventDetail;
        expect(response).toEqual(successResponse);
        expect(error).toBeInstanceOf(HydrationError);
        expect(error.code).toBe(ClientErrorCode.SERVER_ERROR);
        expect(trigger).toBe(unsavedEvent);
        expect(text).toBe('A server error occurred.');
      });

      it('dispatches an error event when fetch fails for any other reason', async () => {
        expect(partialsTarget.innerHTML).toBe('');

        fetch.mockImplementationOnce(() =>
          Promise.resolve({
            // Unlikely but possible case where fetch resolves but
            // reading the body fails
            text: () => Promise.reject(new Error('Unexpected error')),
            ok: true,
            status: 200,
            statusText: 'OK',
          }),
        );

        const errorEvent = new Promise((resolve) => {
          form.addEventListener('w-autosave:error', (event) => resolve(event), {
            once: true,
          });
        });

        const unsavedEvent = await dispatchUnsaved(form);
        await jest.advanceTimersByTimeAsync(500);

        expect(fetch).toHaveBeenCalledTimes(2);
        expect(fetch.mock.calls[1][0]).toBe(
          '/edit/123/?_w_hydrate_create_view=1',
        );

        const { detail: errorEventDetail } = await errorEvent;

        const { response, error, trigger, text } = errorEventDetail;
        expect(response).toEqual(successResponse);
        expect(error).toBeInstanceOf(HydrationError);
        expect(error.code).toBe(ClientErrorCode.SERVER_ERROR);
        expect(trigger).toBe(unsavedEvent);
        expect(text).toBe('A server error occurred.');
      });
    });
  });

  describe('error handling for autosave requests', () => {
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

    it('deactivates autosave after an invalid_revision error', async () => {
      const form = await setup();

      const serverResponse = {
        success: false,
        error_code: 'invalid_revision',
        error_message: 'Invalid revision',
      };

      fetch.mockResponseBadRequest(JSON.stringify(serverResponse));

      const deactivatedEvent = new Promise((resolve) => {
        form.addEventListener(
          'w-autosave:deactivated',
          (event) => resolve(event),
          {
            once: true,
          },
        );
      });
      const errorEvent = new Promise((resolve) => {
        form.addEventListener('w-autosave:error', (event) => resolve(event), {
          once: true,
        });
      });

      const unsavedEvent1 = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);
      expect(fetch).toHaveBeenCalledTimes(1);

      const { detail: deactivatedEventDetail } = await deactivatedEvent;
      expect(deactivatedEventDetail.response).toEqual(serverResponse);
      expect(deactivatedEventDetail.error).toBeInstanceOf(Error);
      expect(deactivatedEventDetail.error.message).toBe('Invalid revision');
      expect(deactivatedEventDetail.trigger).toBe(unsavedEvent1);

      const { detail: errorEventDetail } = await errorEvent;
      expect(errorEventDetail.response).toEqual(serverResponse);
      expect(errorEventDetail.error).toBeInstanceOf(Error);
      expect(errorEventDetail.error.message).toBe('Invalid revision');
      expect(errorEventDetail.trigger).toBe(unsavedEvent1);

      // Should have deactivated autosave
      expect(form.getAttribute('data-w-autosave-active-value')).toBe('false');

      // Subsequent unsaved events do not trigger autosave
      const unsavedEvent2 = await dispatchUnsaved(form);
      await jest.advanceTimersByTimeAsync(500);
      expect(fetch).toHaveBeenCalledTimes(1); // still 1, no new call
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

  describe('indicator behavior', () => {
    let form;

    beforeEach(async () => {
      form = await setup();
      document.body.insertAdjacentHTML(
        'beforeend',
        /* html */ `
        <div
          id="w-autosave-indicator"
          data-controller="w-tooltip w-autosave"
          data-w-tooltip-content-value=""
          data-action="
            w-autosave:save@document->w-autosave#updateIndicator
            w-autosave:success@document->w-autosave#updateIndicator
            w-autosave:error@document->w-autosave#updateIndicator
            unknown-event@document->w-autosave#updateIndicator
          "
        >
        </div>
      `,
      );
      await Promise.resolve();
    });

    it('updates the state value and tooltip content based on events', async () => {
      const indicator = document.getElementById('w-autosave-indicator');

      const getIndicatorState = () =>
        indicator.getAttribute('data-w-autosave-state-value');
      const getTooltipContent = () =>
        indicator.getAttribute('data-w-tooltip-content-value');

      // Initial state
      expect(getIndicatorState()).toBe(null);
      expect(getTooltipContent()).toBe('');

      // On save
      const saveEvent = new CustomEvent('w-autosave:save', {
        bubbles: true,
      });
      form.dispatchEvent(saveEvent);
      await Promise.resolve();

      expect(getIndicatorState()).toBe('saving');
      expect(getTooltipContent()).toBe('Autosave in progress…');

      // On success
      const successEvent = new CustomEvent('w-autosave:success', {
        bubbles: true,
      });
      form.dispatchEvent(successEvent);
      await Promise.resolve();

      expect(getIndicatorState()).toBe('saved');
      expect(getTooltipContent()).toBe('Changes have been autosaved.');

      // On error
      const errorEvent = new CustomEvent('w-autosave:error', {
        bubbles: true,
        detail: {
          text: 'Some error text.',
        },
      });
      form.dispatchEvent(errorEvent);
      await Promise.resolve();

      expect(getIndicatorState()).toBe('paused');
      expect(getTooltipContent()).toBe('Some error text.');

      // On unknown event - should default to idle
      const unknownEvent = new CustomEvent('unknown-event', {
        bubbles: true,
      });
      form.dispatchEvent(unknownEvent);
      await Promise.resolve();

      expect(getIndicatorState()).toBe('idle');
      expect(getTooltipContent()).toBe('');
    });
  });
});
