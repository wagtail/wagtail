import { Application } from '@hotwired/stimulus';

import { AutoFormController } from './AutoFormController';

describe('AutoFormController', () => {
  const requestSubmit = jest.fn();

  beforeAll(() => {
    window.HTMLFormElement.prototype.requestSubmit = requestSubmit;

    document.body.innerHTML = `
  <form>
    <select name="order" data-controller="w-auto-form" data-action="change->w-auto-form#submit" value="A-Z">
      <option value="A-Z" selected>A to Z</option>
      <option value="Z-A">Z to A</option> 
    </select>
  </form>
  `;

    Application.start().register('w-auto-form', AutoFormController);
  });

  it('should expose a submit method that can be attached to an action', () => {
    expect(requestSubmit).not.toHaveBeenCalled();

    const select = document.querySelector('select');
    select.value = 'Z-A';
    select.dispatchEvent(new CustomEvent('change'));

    expect(requestSubmit).toHaveBeenCalled();
  });
});
