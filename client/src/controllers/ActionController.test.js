import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';

describe('ActionController', () => {
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
    Application.start().register('w-action', ActionController);
  });

  it('it should enable the workflow on click', () => {
    const btn = document.querySelector('[data-controller="w-action"]');
    const submitMock = jest.fn();
    window.HTMLFormElement.prototype.submit = submitMock;

    btn.click();

    const form = document.querySelector('form');

    expect(submitMock).toHaveBeenCalled();
    expect(form.action).toBe('https://www.github.com/');
    expect(new FormData(form).get('csrfmiddlewaretoken')).toBe('potato');
  });
});
