import { validateCreationForm } from './chooserModal';

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
});
