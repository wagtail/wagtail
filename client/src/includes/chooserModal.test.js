import $ from 'jquery';
import { SearchController, validateCreationForm } from './chooserModal';

jest.useFakeTimers();

describe('chooserModal', () => {
  describe('SearchController', () => {
    let form;
    let controller;
    let ajaxSpy;

    beforeEach(() => {
      document.body.innerHTML = `
        <form action="/chooser/" method="GET">
          <div id="layout" data-chooser-modal-search-filter>
            <input type="radio" name="layout" value="grid" />
            <input type="radio" name="layout" value="list" />
          </div>
          <input name="q" value="" />
        </form>
        <div id="results"></div>`;
      form = $('form');
      controller = new SearchController({
        form,
        containerElement: document.body,
        resultsContainerSelector: '#results',
      });
      controller.attachSearchFilter('[data-chooser-modal-search-filter]');
      controller.attachSearchInput('input[name="q"]');
      ajaxSpy = jest
        .spyOn($, 'ajax')
        .mockImplementation(() => ({ abort: jest.fn() }));
    });

    afterEach(() => {
      ajaxSpy.mockRestore();
    });

    it('preserves the current page when the layout changes', () => {
      controller.fetchResults('/chooser/?p=3');
      $('input[name="layout"][value="list"]').prop('checked', true);
      $('input[name="layout"][value="list"]').trigger('change');

      expect(ajaxSpy).toHaveBeenLastCalledWith(
        expect.objectContaining({
          url: '/chooser/',
          data: expect.stringContaining('p=3'),
        }),
      );
    });

    it('does not preserve the current page for other filters', () => {
      controller.fetchResults('/chooser/?p=3');
      $('input[name="q"]').val('cats');
      $('input[name="q"]').trigger('input');
      jest.runOnlyPendingTimers();

      expect(ajaxSpy).toHaveBeenLastCalledWith(
        expect.objectContaining({
          data: 'q=cats',
        }),
      );
    });
  });

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
