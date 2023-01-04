import { Application } from '@hotwired/stimulus';
import { ActionController } from './ActionController';

describe('ActionController', () => {
  document.body.innerHTML = `
    <button data-controller="w-action"
    data-w-action-csrf-token-value = "hiudsghds89763nxcksj"
    data-w-action-key-name-value = 'csrfmiddlewaretoken'
    data-w-action-post-url-value = "https://www.github.com"
    class="button no"
    id="select-button"
    data-action="click->w-action#enableAction"
    >Enable</button>
    `;
  Application.start().register('w-action', ActionController);

  it('it should enable the workflow on click', () => {});
});
