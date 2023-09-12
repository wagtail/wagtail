import { Application } from '@hotwired/stimulus';

import { SubmitController } from './SubmitController';

describe('SubmitController', () => {
  beforeEach(() => {
    document.body.innerHTML = `
  <form id="form">
    <select name="order" data-controller="w-submit" data-action="change->w-submit#submit" value="A-Z">
      <option value="A-Z" selected>A to Z</option>
      <option value="Z-A">Z to A</option>
    </select>
  </form>`;

    Application.start().register('w-submit', SubmitController);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should expose a submit method that can be attached to an action that will call requestSubmit on the form', () => {
    let lastFormCalled = null;

    const requestSubmit = jest.fn(function mockRequestSubmit() {
      lastFormCalled = this;
    });

    window.HTMLFormElement.prototype.requestSubmit = requestSubmit;

    const select = document.querySelector('select');
    select.value = 'Z-A';
    select.dispatchEvent(new CustomEvent('change'));

    expect(requestSubmit).toHaveBeenCalled();
    expect(lastFormCalled).toEqual(document.getElementById('form'));
  });

  it('should expose a submit method that can be attached to an action that will call submit if requestSubmit is not available', () => {
    let lastFormCalled = null;

    const submit = jest.fn(function mockSubmit() {
      lastFormCalled = this;
    });

    window.HTMLFormElement.prototype.requestSubmit = null; // mock not being available in a browser
    window.HTMLFormElement.prototype.submit = submit;

    const select = document.querySelector('select');
    select.value = 'Z-A';
    select.dispatchEvent(new CustomEvent('change'));

    expect(submit).toHaveBeenCalled();
    expect(lastFormCalled).toEqual(document.getElementById('form'));
  });
});
