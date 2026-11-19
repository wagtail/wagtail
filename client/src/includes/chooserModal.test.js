import $ from 'jquery';
import { SearchController, validateCreationForm } from './chooserModal';

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

  describe('SearchController', () => {
    let ajax;

    const pagination = `
      <nav class="pagination">
        <ul>
          <li><a href="/admin/images/chooser/results/?layout=grid&p=1">1</a></li>
          <li><a href="/admin/images/chooser/results/?layout=grid&p=2" aria-current="page">2</a></li>
          <li><a href="/admin/images/chooser/results/?layout=grid&p=3">3</a></li>
        </ul>
      </nav>`;

    const setup = (results = pagination) => {
      document.body.innerHTML = `
      <div id="modal">
        <form data-chooser-modal-search action="/admin/images/chooser/results/">
          <input id="id_q" name="q" type="text" value="" />
          <select id="collection" name="collection_id" data-chooser-modal-search-filter>
            <option value="">All</option>
            <option value="2">Other</option>
          </select>
          <div id="layout" data-chooser-modal-search-filter data-chooser-modal-search-keep-page>
            <input type="radio" name="layout" value="grid" checked />
            <input type="radio" name="layout" value="list" />
          </div>
        </form>
        <div id="search-results">${results}</div>
      </div>`;

      const modal = document.getElementById('modal');
      const controller = new SearchController({
        form: $(modal.querySelector('form[data-chooser-modal-search]')),
        containerElement: modal,
        resultsContainerSelector: '#search-results',
      });
      controller.attachSearchFilter('[data-chooser-modal-search-filter]');
      return controller;
    };

    const selectListLayout = () => {
      const listLayout = document.querySelector(
        '[name="layout"][value="list"]',
      );
      listLayout.checked = true;
      listLayout.dispatchEvent(new Event('change', { bubbles: true }));
    };

    beforeEach(() => {
      ajax = jest.spyOn($, 'ajax').mockImplementation(() => ({}));
    });

    afterEach(() => {
      ajax.mockRestore();
    });

    it('should keep the current page when changing a filter that keeps the page', () => {
      setup();

      selectListLayout();

      expect(ajax).toHaveBeenCalledTimes(1);
      expect(ajax.mock.lastCall[0]).toMatchObject({
        url: '/admin/images/chooser/results/',
        data: 'q=&collection_id=&layout=list&p=2',
      });
    });

    it('should go back to the first page when changing any other filter', () => {
      setup();

      const collection = document.getElementById('collection');
      collection.value = '2';
      collection.dispatchEvent(new Event('change', { bubbles: true }));

      expect(ajax).toHaveBeenCalledTimes(1);
      expect(ajax.mock.lastCall[0].data).toEqual(
        'q=&collection_id=2&layout=grid',
      );
    });

    it('should not add a page when the results are not paginated', () => {
      setup('<p>There are no results.</p>');

      selectListLayout();

      expect(ajax).toHaveBeenCalledTimes(1);
      expect(ajax.mock.lastCall[0].data).toEqual(
        'q=&collection_id=&layout=list',
      );
    });
  });
});
