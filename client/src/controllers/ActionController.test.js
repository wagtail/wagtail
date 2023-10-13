import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';

describe('ActionController', () => {
  let app;
  const oldWindowLocation = window.location;

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    app = Application.start();
    app.register('w-action', ActionController);

    await Promise.resolve();
  };

  beforeAll(() => {
    delete window.location;

    window.location = Object.defineProperties(
      {},
      {
        ...Object.getOwnPropertyDescriptors(oldWindowLocation),
        assign: { configurable: true, value: jest.fn() },
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

    it('it should allow for a form POST with created data', () => {
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
      const clickMock = jest.fn();
      HTMLButtonElement.prototype.click = clickMock;

      btn.addEventListener('some-event', btn.click());

      const event = new CustomEvent('some-event');
      btn.dispatchEvent(event);

      expect(clickMock).toHaveBeenCalled();
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
    beforeEach(async () => {
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
    });

    it('select should be called when you click on text in textarea', () => {
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
});
