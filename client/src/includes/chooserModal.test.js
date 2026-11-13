import {
  ChooserModalOnloadHandlerFactory,
  validateCreationForm,
} from './chooserModal';

jest.useFakeTimers();

describe('chooserModal', () => {
  describe('validateCreationForm', () => {
    let form;

    beforeEach(() => {
      document.body.innerHTML = `
      <form id="form">
        <div data-field>
          <div data-field-errors></div>
          <input id="input" required type="text" />
        </div>
        <button id="button" type="submit" data-controller="w-progress" data-w-progress-loading-value="true">Update</button>
      </form>`;

      form = document.getElementById('form');
    });

    afterEach(() => {
      jest.runAllTimers();
    });

    it('should update the aria attribute on invalid fields', () => {
      const input = document.getElementById('input');

      expect(input.getAttribute('aria-invalid')).toBeFalsy();

      validateCreationForm(form);

      expect(input.getAttribute('aria-invalid')).toBeTruthy();
    });

    it('should append an error message', () => {
      expect(form.querySelector('.error-message')).toBeFalsy();

      validateCreationForm(form);

      expect(form.querySelector('.error-message').innerHTML).toEqual(
        'This field is required.',
      );
    });

    it('should clear any in progress buttons', () => {
      const button = document.getElementById('button');

      validateCreationForm(form);

      expect({ ...button.dataset }).toEqual({
        controller: 'w-progress',
        wProgressLoadingValue: 'true',
      });

      jest.runAllTimers();

      expect({ ...button.dataset }).toEqual({
        controller: 'w-progress',
      });
    });
  });

  describe('ChooserModalOnloadHandlerFactory.ajaxifyLinks', () => {
    let factory;
    let modal;

    beforeEach(() => {
      document.body.innerHTML = `
      <div id="container">
        <button type="button" data-chooser-modal-choice data-chooser-modal-choice-url="/chosen/1/">Button choice</button>
        <a data-chooser-modal-choice href="/chosen/2/">Link choice</a>
      </div>`;

      factory = new ChooserModalOnloadHandlerFactory();
      factory.searchController = {};
      modal = { loadUrl: jest.fn(), body: document.body };
      factory.ajaxifyLinks(modal, document.getElementById('container'));
    });

    it('should load the URL from the data attribute for button choices', () => {
      document.querySelector('button').click();
      expect(modal.loadUrl).toHaveBeenCalledWith('/chosen/1/');
    });

    it('should load the URL from the href for link choices', () => {
      document.querySelector('a').click();
      expect(modal.loadUrl).toHaveBeenCalledWith('http://localhost/chosen/2/');
    });
  });
});
