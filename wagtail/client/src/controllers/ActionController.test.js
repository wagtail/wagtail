import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';
import { UnsavedController } from './UnsavedController';

describe('ActionController', () => {
  let app;
  const oldWindowLocation = window.location;

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    app = Application.start();
    app.register('w-action', ActionController);
    app.register('w-unsaved', UnsavedController);

    await Promise.resolve();
  };

  beforeAll(() => {
    delete window.location;

    window.location = Object.defineProperties(
      {},
      {
        ...Object.getOwnPropertyDescriptors(oldWindowLocation),
        assign: { configurable: true, value: jest.fn() },
        reload: {
          configurable: true,
          value: jest.fn().mockImplementation(() => {
            const event = new Event('beforeunload', { cancelable: true });
            window.dispatchEvent(event);
          }),
        },
      },
    );
  });

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('post method', () => {
    beforeEach(async () => {
      await setup(`
      <button
        class="button no"
        data-controller="w-action"
        data-action="w-action#post"
        data-w-action-url-value="https://www.github.com"
      >
        Enable
      </button>`);
    });

    it('should allow for a form POST with created data', () => {
      const btn = document.querySelector('[data-controller="w-action"]');
      const submitMock = jest.fn();
      window.HTMLFormElement.prototype.submit = submitMock;

      btn.click();
      const form = document.querySelector('form');

      expect(submitMock).toHaveBeenCalled();
      expect(form.action).toBe('https://www.github.com/');
      expect(new FormData(form).get('csrfmiddlewaretoken')).toBe('potato');
      expect(new FormData(form).get('next')).toBe('http://localhost/');
    });
  });

  describe('sendBeacon method', () => {
    beforeEach(async () => {
      await setup(`
      <button
        data-controller="w-action"
        data-action="blur->w-action#sendBeacon"
        data-w-action-url-value="https://analytics.example/not-interested"
      >
        If you move focus away from this button, a POST request will be sent.
      </button>
      <button id="other-button">Other button</button>
      `);
    });

    it('should send a POST request using sendBeacon with the CSRF token included', () => {
      const sendBeaconMock = jest.fn();
      Object.defineProperty(window.navigator, 'sendBeacon', {
        value: sendBeaconMock,
      });

      const btn = document.querySelector('[data-controller="w-action"]');
      const otherBtn = document.getElementById('other-button');
      btn.focus();
      otherBtn.focus();

      expect(sendBeaconMock).toHaveBeenCalledTimes(1);
      expect(sendBeaconMock).toHaveBeenCalledWith(
        'https://analytics.example/not-interested',
        expect.any(FormData),
      );

      const formData = sendBeaconMock.mock.lastCall[1];
      expect(
        Object.fromEntries(formData.entries()).csrfmiddlewaretoken,
      ).toEqual('potato');
    });
  });

  describe('click method', () => {
    beforeEach(async () => {
      await setup(`
      <button
        type="button"
        id="button"
        data-controller="w-action"
        data-action="some-event->w-action#click"
      >
        Button
      </button>`);
    });

    it('should call click method when button is clicked via Stimulus action', () => {
      const btn = document.getElementById('button');
      const clickMock = jest.spyOn(HTMLButtonElement.prototype, 'click');

      const event = new CustomEvent('some-event');
      btn.dispatchEvent(event);

      expect(clickMock).toHaveBeenCalled();
    });
  });

  describe('reload method', () => {
    beforeEach(async () => {
      await setup(`
      <button
        id="button"
        data-controller="w-action"
        data-action="click->w-action#reload"
      >
        Reload
      </button>`);
    });

    it('should reload the page', () => {
      const beforeUnloadHandler = jest.fn();
      window.addEventListener('beforeunload', beforeUnloadHandler);

      document.getElementById('button').click();

      expect(window.location.reload).toHaveBeenCalledTimes(1);
      expect(beforeUnloadHandler).toHaveBeenCalledTimes(1);

      const event = beforeUnloadHandler.mock.lastCall[0];
      // This means the browser confirmation dialog was not shown
      expect(event.defaultPrevented).toBe(false);

      window.removeEventListener('beforeunload', beforeUnloadHandler);
    });

    it('should not bypass the browser confirmation dialog if the event is prevented', async () => {
      document.body.innerHTML = /* html */ `
      <form
        data-controller="w-unsaved"
        data-action="beforeunload@window->w-unsaved#confirm"
        data-w-unsaved-confirmation-value="true"
      >
      </form>
      <button
        id="button"
        data-controller="w-action"
        data-action="click->w-action#reload"
      >
        Reload
      </button>
      `;
      await Promise.resolve();

      // Simulate having unsaved changes by setting has-edits-value to true.
      // We can't set this on init because the value is set to false on connect.
      document
        .querySelector('form')
        .setAttribute('data-w-unsaved-has-edits-value', 'true');
      await Promise.resolve();
      const beforeUnloadHandler = jest.fn();
      window.addEventListener('beforeunload', beforeUnloadHandler);

      document.getElementById('button').click();

      expect(window.location.reload).toHaveBeenCalledTimes(1);
      expect(beforeUnloadHandler).toHaveBeenCalledTimes(1);

      const event = beforeUnloadHandler.mock.lastCall[0];
      // This means the browser confirmation dialog was shown
      expect(event.defaultPrevented).toBe(true);
      window.removeEventListener('beforeunload', beforeUnloadHandler);
    });
  });

  describe('forceReload method', () => {
    beforeEach(async () => {
      await setup(/* html */ `
      <form
        data-controller="w-unsaved"
        data-action="beforeunload@window->w-unsaved#confirm"
        data-w-unsaved-confirmation-value="true"
      >
      </form>
      <button
        id="button"
        data-controller="w-action"
        data-action="click->w-action#forceReload"
      >
        Force reload
      </button>`);

      // Simulate having unsaved changes by setting has-edits-value to true.
      // We can't set this on init because the value is set to false on connect.
      document
        .querySelector('form')
        .setAttribute('data-w-unsaved-has-edits-value', 'true');
      await Promise.resolve();
    });

    it('should reload the page without showing the browser confirmation dialog', () => {
      const confirmHandler = jest.fn();
      const beforeUnloadHandler = jest.fn();
      document.addEventListener('w-unsaved:confirm', confirmHandler);
      window.addEventListener('beforeunload', beforeUnloadHandler);

      document.getElementById('button').click();

      expect(window.location.reload).toHaveBeenCalledTimes(1);
      expect(beforeUnloadHandler).toHaveBeenCalledTimes(1);

      const beforeUnloadEvent = beforeUnloadHandler.mock.lastCall[0];
      // If the browser confirmation was shown, this would be true
      expect(beforeUnloadEvent.defaultPrevented).toBe(false);

      expect(confirmHandler).toHaveBeenCalledTimes(1);
      const confirmEvent = confirmHandler.mock.lastCall[0];
      // We're preventing UnsavedController from triggering the browser confirmation
      expect(confirmEvent.defaultPrevented).toBe(true);

      window.removeEventListener('beforeunload', beforeUnloadHandler);
      document.removeEventListener('w-unsaved:confirm', confirmHandler);
    });
  });

  describe('redirect method', () => {
    beforeEach(async () => {
      await setup(`
      <select name="url" data-controller="w-action" data-action="change->w-action#redirect">
        <option value="http://localhost/place?option=1">1</option>
        <option value="http://localhost/place?option=2" selected>2</option>
      </select>`);
    });

    it('should have a redirect method that falls back to any element value', () => {
      const select = document.querySelector('select');

      expect(window.location.href).toEqual('http://localhost/');
      expect(window.location.assign).not.toHaveBeenCalled();

      select.dispatchEvent(new CustomEvent('change'));

      expect(window.location.assign).toHaveBeenCalledWith(
        'http://localhost/place?option=2',
      );
    });

    it('should allow redirection via the custom event detail', () => {
      const select = document.querySelector('select');

      expect(window.location.href).toEqual('http://localhost/');
      expect(window.location.assign).not.toHaveBeenCalled();

      select.dispatchEvent(
        new CustomEvent('change', { detail: { url: '/its/in/the/detail/' } }),
      );

      expect(window.location.assign).toHaveBeenCalledWith(
        '/its/in/the/detail/',
      );
    });

    it('should allow redirection via the Stimulus param approach', () => {
      const select = document.querySelector('select');

      expect(window.location.href).toEqual('http://localhost/');
      expect(window.location.assign).not.toHaveBeenCalled();

      select.dataset.wActionUrlParam = '/check/out/the/param/';

      select.dispatchEvent(
        new CustomEvent('change', { detail: { url: '/its/in/the/detail/' } }),
      );

      expect(window.location.assign).toHaveBeenCalledWith(
        '/check/out/the/param/',
      );
    });

    it('should allow redirection blocking via the event detail', () => {
      const select = document.querySelector('select');

      expect(window.location.href).toEqual('http://localhost/');
      expect(window.location.assign).not.toHaveBeenCalled();

      // setting to a non-null/undefined value should allow blocking
      select.dispatchEvent(new CustomEvent('change', { detail: { url: '' } }));
      select.dispatchEvent(
        new CustomEvent('change', { detail: { url: false } }),
      );

      expect(window.location.assign).not.toHaveBeenCalled();
    });

    it('should allow redirection blocking via the Stimulus param approach', () => {
      const select = document.querySelector('select');

      expect(window.location.href).toEqual('http://localhost/');
      expect(window.location.assign).not.toHaveBeenCalled();

      // setting to a non-null/undefined value should allow blocking
      select.dataset.wActionUrlParam = '';

      select.dispatchEvent(new CustomEvent('change'));

      expect(window.location.assign).not.toHaveBeenCalled();
    });
  });

  describe('select method', () => {
    it('select should be called when you click on text in textarea', async () => {
      await setup(`
        <textarea
          id="text"
          rows="1"
          data-controller="w-action"
          data-action="focus->w-action#select"
        >
          some random text
        </textarea>
      `);

      const textarea = document.getElementById('text');

      // check that there is no selection initially
      expect(textarea.selectionStart).toBe(0);
      expect(textarea.selectionEnd).toBe(0);

      // focus
      textarea.focus();

      // check that there is a selection after focus
      expect(textarea.selectionStart).toBe(0);
      expect(textarea.selectionEnd).toBe(textarea.value.length);
    });

    it('select should be called for for input elements', async () => {
      await setup(`
      <input
        type="text"
        id="input"
        data-controller="w-action"
        data-action="some-event->w-action#select"
        value="some random text"
      />
      `);

      const input = document.getElementById('input');

      // check that there is no selection initially
      expect(input.selectionStart).toBe(0);
      expect(input.selectionEnd).toBe(0);

      const event = new CustomEvent('some-event');
      input.dispatchEvent(event);

      // check that there is a selection after the event
      expect(input.selectionStart).toBe(0);
      expect(input.selectionEnd).toBe(16);
    });

    it('select should not throw errors when called on a button element', async () => {
      await setup(`
        <button
          id="button"
          data-controller="w-action"
          data-action="click->w-action#select"
        >
          Click me
        </button>
      `);

      const button = document.getElementById('button');

      expect(() => button.click()).not.toThrow();
    });
  });

  describe('reset method', () => {
    const handleChangeEvent = jest.fn();
    document.addEventListener('change', handleChangeEvent);

    beforeEach(async () => {
      jest.resetAllMocks();

      await setup(
        `<input
          id="reset-test"
          value="the default"
          type="text"
          data-controller="w-action"
          data-action="some-event->w-action#reset"
        />`,
      );
    });

    it('should change value when existing value and new value are different', () => {
      const input = document.getElementById('reset-test');

      // Change the value to something else (via JS)
      input.value = 'another input value';
      expect(handleChangeEvent).not.toHaveBeenCalled();

      input.dispatchEvent(
        new CustomEvent('some-event', { detail: { value: 'not the default' } }),
      );

      expect(input.value).toBe('not the default');
      expect(input.value).not.toBe('another input value');
      expect(handleChangeEvent).toHaveBeenCalled();
    });

    it('should not change value when current value and new value are the same', () => {
      expect(handleChangeEvent).not.toHaveBeenCalled();
      const input = document.getElementById('reset-test');

      input.dispatchEvent(
        new CustomEvent('some-event', { detail: { value: 'the default' } }),
      );

      expect(input.value).toBe('the default');
      expect(input.value).not.toBe('not the default');
      expect(handleChangeEvent).not.toHaveBeenCalled();
    });

    it('should reset value to a new value supplied via custom event detail', () => {
      expect(handleChangeEvent).not.toHaveBeenCalled();
      const input = document.getElementById('reset-test');

      input.dispatchEvent(
        new CustomEvent('some-event', {
          detail: { value: 'a new value from custom event detail' },
        }),
      );

      expect(input.value).toBe('a new value from custom event detail');
      expect(input.value).not.toBe('the default');
      expect(handleChangeEvent).toHaveBeenCalled();
    });

    it('should reset value to a new value supplied in action param', () => {
      expect(handleChangeEvent).not.toHaveBeenCalled();
      const input = document.getElementById('reset-test');
      input.setAttribute(
        'data-w-action-value-param',
        'a new value from action params',
      );

      input.dispatchEvent(new CustomEvent('some-event'));

      expect(input.value).toBe('a new value from action params');
      expect(handleChangeEvent).toHaveBeenCalled();
    });
  });

  describe('noop method', () => {
    beforeEach(async () => {
      await setup(`
      <button id="button" data-controller="w-action" data-action="w-action#noop:prevent:stop">
        Click me!
      </button>`);
    });

    it('should a noop method that does nothing, enabling use of action options', async () => {
      const button = document.getElementById('button');

      const onClick = jest.fn();
      document.addEventListener('click', onClick);

      button.dispatchEvent(new Event('click', { bubbles: true }));

      expect(onClick).not.toHaveBeenCalled();

      // remove data-action attribute
      await Promise.resolve(button.removeAttribute('data-action'));

      button.dispatchEvent(new Event('click', { bubbles: true }));

      expect(onClick).toHaveBeenCalled();
    });
  });
});
