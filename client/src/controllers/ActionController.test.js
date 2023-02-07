import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';

describe('ActionController', () => {
  let app;
  const oldWindowLocation = window.location;

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
    beforeEach(() => {
      document.body.innerHTML = `
    <button
      class="button no"
      data-controller="w-action"
      data-action="w-action#post"
      data-w-action-url-value="https://www.github.com"
    >
      Enable
    </button>
    `;

      app = Application.start();
      app.register('w-action', ActionController);
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
    beforeEach(() => {
      document.body.innerHTML = `
      <button
        type="button"
        id="button"
        data-controller="w-action"
        data-action="some-event->w-action#click"
      >
        Button
      </button>
      `;

      app = Application.start();
      app.register('w-action', ActionController);
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
    beforeEach(() => {
      document.body.innerHTML = `
      <select name="url" data-controller="w-action" data-action="change->w-action#redirect">
        <option value="http://localhost/place?option=1">1</option>
        <option value="http://localhost/place?option=2" selected>2</option>
      </select>
      `;

      app = Application.start();
      app.register('w-action', ActionController);
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
  });
});
