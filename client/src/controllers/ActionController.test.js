import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';

describe('ActionController', () => {
  let app;

  afterEach(() => {
    app?.stop();
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
});
