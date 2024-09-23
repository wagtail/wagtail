import { setImmediate } from 'timers';
import { Application } from '@hotwired/stimulus';
import { SwapController } from './SwapController';
import { range } from '../utils/range';

jest.useFakeTimers();

jest.spyOn(console, 'error').mockImplementation(() => {});

const flushPromises = () => new Promise(setImmediate);

describe('SwapController', () => {
  let application;
  let handleError;

  const getMockResults = (
    { attrs = ['id="new-results"'], total = 3 } = {},
    arr = range(0, total),
  ) => {
    const items = arr.map((_) => `<li>RESULT ${_}</li>`).join('');
    return `<ul ${attrs.join(' ')}>${items}</ul>`;
  };

  beforeEach(() => {
    application = Application.start();
    application.register('w-swap', SwapController);
    handleError = jest.fn();
    application.handleError = handleError;
  });

  afterEach(() => {
    application.stop();
    document.body.innerHTML = '<main></main>';
    jest.clearAllMocks();
    // Restore any fetch mocks for good measure. Some tests may mock fetch despite
    // expecting it not to be called, leaving fetch in a mocked state for other tests.
    // Some tests also use mockImplementation() instead of the mockResponse*() helpers
    // that use mockImplementationOnce(), which can cause fetch to be mocked indefinitely.
    fetch.mockRestore();
  });

  describe('when results element & src URL value is not available', () => {
    it('should throw an error if no valid selector can be resolved', async () => {
      expect(handleError).not.toHaveBeenCalled();

      document.body.innerHTML = `
      <div id="listing-results"></div>
      <input
        id="search"
        type="text"
        name="q"
        data-controller="w-swap"
        data-w-swap-target-value=""
      />`;

      // trigger next browser render cycle
      await Promise.resolve();

      expect(handleError).toHaveBeenCalledWith(
        expect.objectContaining({ message: "'' is not a valid selector" }),
        'Error connecting controller',
        expect.objectContaining({ identifier: 'w-swap' }),
      );
    });

    it('should throw an error if target element selector cannot resolve a DOM element', async () => {
      expect(handleError).not.toHaveBeenCalled();

      document.body.innerHTML = `
      <div id="listing-results"></div>
      <input
        id="search"
        type="text"
        name="q"
        data-controller="w-swap"
        data-w-swap-src-value="path/to/search"
        data-w-swap-target-value="#resultX"
      />`;

      // trigger next browser render cycle
      await Promise.resolve();

      expect(handleError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Cannot find valid target element at "#resultX"',
        }),
        'Error connecting controller',
        expect.objectContaining({ identifier: 'w-swap' }),
      );
    });

    it('should throw an error if no valid src URL can be resolved', async () => {
      expect(handleError).not.toHaveBeenCalled();

      document.body.innerHTML = `
      <div id="results"></div>
      <input
        id="search"
        type="text"
        name="q"
        data-controller="w-swap"
        data-w-swap-target-value="#results"
      />`;

      // trigger next browser render cycle
      await Promise.resolve();

      expect(handleError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Cannot find valid src URL value' }),
        'Error connecting controller',
        expect.objectContaining({ identifier: 'w-swap' }),
      );
    });
  });

  describe('performing a location update via actions on a controlled input', () => {
    beforeEach(() => {
      document.body.innerHTML = `
      <form class="search-form" action="/admin/images/" method="get" role="search">
        <div class="w-field__input">
          <svg class="icon icon-search" aria-hidden="true"><use href="#icon-search"></use></svg>
          <input
            id="search"
            type="text"
            name="q"
            data-controller="w-swap"
            data-action="keyup->w-swap#searchLazy"
            data-w-swap-src-value="/admin/images/results/"
            data-w-swap-target-value="#results"
          />
        </div>
      </form>
      <div id="results"></div>
      `;

      window.history.replaceState(null, '', '?');
    });

    it('should not do a location based update if the URL query and the input query are equal', () => {
      const input = document.getElementById('search');

      // when values are empty
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      jest.runAllTimers(); // update is debounced
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      // when input value only has whitespace
      input.value = '   ';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      jest.runAllTimers(); // update is debounced
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      // when input value and URL query only have whitespace
      window.history.replaceState(null, '', '?q=%20%20&p=foo'); // 2 spaces
      input.value = '    '; // 4 spaces
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      jest.runAllTimers(); // update is debounced
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      // when input value and URL query have the same value
      window.history.replaceState(null, '', '?q=espresso');
      input.value = 'espresso';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      jest.runAllTimers(); // update is debounced
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      // when input value and URL query have the same value (ignoring whitespace)
      window.history.replaceState(null, '', '?q=%20espresso%20');
      input.value = '  espresso ';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      jest.runAllTimers(); // update is debounced
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should allow for updating via a declared action on input changes', async () => {
      const input = document.getElementById('search');
      const icon = document.querySelector('.icon-search use');
      const targetElement = document.getElementById('results');

      const results = getMockResults();

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();
      expect(icon.getAttribute('href')).toEqual('#icon-search');
      expect(targetElement.getAttribute('aria-busy')).toBeNull();

      input.value = 'alpha';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      jest.runAllTimers(); // update is debounced

      // visual loading state should be active & content busy
      await Promise.resolve(); // trigger next rendering
      expect(targetElement.getAttribute('aria-busy')).toEqual('true');
      expect(icon.getAttribute('href')).toEqual('#icon-spinner');

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/admin/images/results/?q=alpha',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/admin/images/results/?q=alpha',
        results,
      });

      // should update HTML
      expect(targetElement.querySelectorAll('li')).toHaveLength(3);

      await flushPromises();

      // should update the current URL
      expect(window.location.search).toEqual('?q=alpha');

      // should reset the icon & busy state
      expect(icon.getAttribute('href')).toEqual('#icon-search');
      expect(targetElement.getAttribute('aria-busy')).toBeNull();
    });

    it('should correctly clear any params based on the action param value', async () => {
      const MOCK_SEARCH = '?k=keep&q=alpha&r=remove-me&s=stay&x=exclude-me';
      window.history.replaceState(null, '', MOCK_SEARCH);
      const input = document.getElementById('search');

      // update clear param - check we can handle space separated values
      input.setAttribute('data-w-swap-clear-param', 'r x');

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(getMockResults()),
        }),
      );

      expect(window.location.search).toEqual(MOCK_SEARCH);

      input.value = 'beta';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      // run all timers & promises
      await flushPromises(jest.runAllTimers());

      // should update the current URL
      expect(window.location.search).toEqual('?k=keep&q=beta&s=stay');
    });

    it('should handle both clearing values in the URL and using a custom query param from input', async () => {
      const MOCK_SEARCH = '?k=keep&query=alpha&r=remove-me';
      window.history.replaceState(null, '', MOCK_SEARCH);
      const input = document.getElementById('search');
      input.setAttribute('name', 'query');

      // update clear param value to a single (non-default) value
      input.setAttribute('data-w-swap-clear-param', 'r');

      fetch.mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(getMockResults()),
        }),
      );

      expect(window.location.search).toEqual(MOCK_SEARCH);

      input.value = 'a new search string!';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      // run all timers & promises
      await flushPromises(jest.runAllTimers());

      // should update the current URL, removing any cleared params
      expect(window.location.search).toEqual(
        '?k=keep&query=a+new+search+string%21',
      );

      // should clear the location params if the input is updated to an empty value
      input.value = '';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      // run all timers & promises
      await flushPromises(jest.runAllTimers());

      // should update the current URL, removing the query param
      expect(window.location.search).toEqual('?k=keep');
    });

    it('should handle repeated input and correctly resolve the requested data', async () => {
      window.history.replaceState(null, '', '?q=first&p=3');

      const input = document.getElementById('search');

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const delays = [200, 20, 400]; // emulate changing results timings

      fetch.mockImplementation(
        (query) =>
          new Promise((resolve) => {
            const delay = delays.pop();
            setTimeout(() => {
              resolve({
                ok: true,
                status: 200,
                text: () =>
                  Promise.resolve(
                    getMockResults({
                      attrs: [
                        'id="new-results"',
                        `data-query="${query}"`,
                        `data-delay="${delay}"`,
                      ],
                    }),
                  ),
              });
            }, delay);
          }),
      );

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      setTimeout(() => {
        input.value = 'beta';
        input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      }, 210);

      setTimeout(() => {
        input.value = 'delta';
        input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));
      }, 420);

      jest.runAllTimers(); // update is debounced

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledTimes(3);
      expect(global.fetch).toHaveBeenLastCalledWith(
        '/admin/images/results/?q=delta',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/admin/images/results/?q=beta',
        results: expect.any(String),
      });

      // should update HTML
      const resultsElement = document.getElementById('results');
      expect(resultsElement.querySelectorAll('li')).toHaveLength(3);
      expect(
        resultsElement.querySelector('[data-query]').dataset.query,
      ).toEqual('/admin/images/results/?q=delta');

      await flushPromises();

      // should update the current URL & clear the page param
      expect(window.location.search).toEqual('?q=delta');
    });

    it('should handle search results API failures gracefully', async () => {
      const icon = document.querySelector('.icon-search use');
      const input = document.getElementById('search');

      const onErrorEvent = jest.fn();
      document.addEventListener('w-swap:error', onErrorEvent);

      fetch.mockResponseFailure();

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      input.dispatchEvent(new CustomEvent('keyup', { bubbles: true }));

      jest.runAllTimers(); // update is debounced

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/admin/images/results/?q=alpha',
        expect.any(Object),
      );

      expect(onErrorEvent).not.toHaveBeenCalled();

      await Promise.resolve(); // trigger next rendering
      expect(icon.getAttribute('href')).toEqual('#icon-spinner');

      await flushPromises(); // resolve all promises

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenLastCalledWith(
        'Error fetching %s',
        '/admin/images/results/?q=alpha',
        expect.any(Error),
      );

      // should not update any HTML
      expect(document.getElementById('results').innerHTML).toEqual('');

      // should have dispatched a custom event for the error
      expect(onErrorEvent).toHaveBeenCalledTimes(1);
      expect(onErrorEvent.mock.calls[0][0].detail).toEqual({
        error: expect.any(Error),
        requestUrl: '/admin/images/results/?q=alpha',
      });

      await Promise.resolve(); // trigger next rendering

      // should reset the icon
      expect(icon.getAttribute('href')).toEqual('#icon-search');
    });
  });

  describe('performing a location update via actions on a controlled form', () => {
    beforeEach(() => {
      document.body.innerHTML = `
      <form
        class="search-form"
        action="/path/to/form/action/"
        method="get"
        role="search"
        data-controller="w-swap"
        data-action="input->w-swap#searchLazy"
        data-w-swap-target-value="#other-results"
      >
        <div class="w-field__input">
          <svg class="icon icon-search" aria-hidden="true"><use href="#icon-search"></use></svg>
          <input id="search" type="text" name="q" data-w-swap-target="input"/>
        </div>
      </form>
      <div id="other-results"></div>
      `;

      window.history.replaceState(null, '', '?');
    });

    it('should allow for searching via a declared action on input changes', async () => {
      const input = document.getElementById('search');
      const icon = document.querySelector('.icon-search use');

      const results = getMockResults();

      const onBegin = jest.fn();
      document.addEventListener('w-swap:begin', onBegin);

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();
      expect(icon.getAttribute('href')).toEqual('#icon-search');

      input.value = 'alpha';
      input.dispatchEvent(new CustomEvent('input', { bubbles: true }));

      jest.runAllTimers(); // update is debounced

      expect(onBegin).toHaveBeenCalledTimes(1);

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering
      expect(icon.getAttribute('href')).toEqual('#icon-spinner');

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/form/action/?q=alpha',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/form/action/?q=alpha',
        results,
      });

      // should update HTML
      expect(
        document.getElementById('other-results').querySelectorAll('li'),
      ).toHaveLength(3);

      await flushPromises();

      // should update the current URL
      expect(window.location.search).toEqual('?q=alpha');

      // should reset the icon
      expect(icon.getAttribute('href')).toEqual('#icon-search');

      expect(onBegin).toHaveBeenCalledTimes(1);
    });

    it('should allow for blocking the request with custom events', async () => {
      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const beginEventHandler = jest.fn((event) => {
        event.preventDefault();
      });

      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      input.dispatchEvent(new CustomEvent('input', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced
      await Promise.resolve();

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/form/action/?q=alpha',
      });

      expect(global.fetch).not.toHaveBeenCalled();

      document.removeEventListener('w-swap:begin', beginEventHandler);
    });
  });

  describe('performing a content update via actions on a controlled button without a form', () => {
    beforeEach(() => {
      document.body.innerHTML = `
      <button
        id="clear"
        data-controller="w-swap"
        data-action="w-swap#replaceLazy"
        data-w-swap-src-value="/admin/custom/results/?type=bar"
        data-w-swap-target-value="#results"
      >Clear owner filter</button>
      <div id="results"></div>
      `;
    });

    it('should default the request method to GET', async () => {
      const button = document.getElementById('clear');
      const targetElement = document.getElementById('results');

      const results = getMockResults();

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      fetch.mockResponseSuccessText(results);

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();
      expect(targetElement.getAttribute('aria-busy')).toBeNull();

      button.click();

      jest.runAllTimers(); // update is debounced

      // the content should be marked as busy
      await Promise.resolve(); // trigger next rendering
      expect(targetElement.getAttribute('aria-busy')).toEqual('true');

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/admin/custom/results/?type=bar',
        expect.objectContaining({
          method: 'GET',
          body: undefined,
        }),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/admin/custom/results/?type=bar',
        results,
      });

      // should update HTML
      expect(targetElement.querySelectorAll('li')).toHaveLength(3);

      await flushPromises();

      // should reset the busy state
      expect(targetElement.getAttribute('aria-busy')).toBeNull();
    });
  });

  describe('performing a content update via actions on a controlled form without using form values', () => {
    let beginEventHandler;
    let formElement;
    let onSuccess;
    const results = getMockResults({ total: 2 });

    beforeEach(() => {
      document.body.innerHTML = /* html */ `
      <main>
      <form
        id="form"
        action="/path/to/form/action/"
        method="get"
        data-controller="w-swap"
        data-action="custom:event->w-swap#replaceLazy submit:prevent->w-swap#replace"
        data-w-swap-target-value="#content"
      >
        <input type="text" name="foo-unused" value="bar-unused" />
        <button type="submit">Submit</button>
      </form>
      <div id="content"></div>
      </main>
      `;

      window.history.replaceState(null, '', '?');

      formElement = document.getElementById('form');

      onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);
    });

    it('should allow for actions to call the replace method directly, defaulting to the form action url', async () => {
      const expectedRequestUrl = '/path/to/form/action/';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      expect(window.location.search).toEqual('');
    });

    it('should support replace with a src value', async () => {
      const expectedRequestUrl = '/path/to-src-value/';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      formElement.setAttribute('data-w-swap-src-value', expectedRequestUrl);

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      expect(window.location.search).toEqual('');
    });

    it('should support using the form method as the fetch request method', async () => {
      const expectedRequestUrl = '/path/to-src-value/?with=param';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      formElement.setAttribute('data-w-swap-src-value', expectedRequestUrl);
      formElement.setAttribute('method', 'post');

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.objectContaining({
          headers: {
            'x-requested-with': 'XMLHttpRequest',
            'x-xsrf-token': 'potato',
          },
          method: 'POST',
        }),
      );
      // We are using #replace, not #submit, so we should not have a body
      expect(global.fetch.mock.lastCall[1].body).toBeUndefined();

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      expect(window.location.search).toEqual('');
    });

    it('should reflect the query params of the request URL if reflect-value is true', async () => {
      const expectedRequestUrl = '/path/to-src-value/?foo=bar&abc=&xyz=123';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      const reflectEventHandler = new Promise((resolve) => {
        document.addEventListener('w-swap:reflect', resolve);
      });

      formElement.setAttribute('data-w-swap-src-value', expectedRequestUrl);
      formElement.setAttribute('data-w-swap-reflect-value', 'true');

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const reflectEvent = await reflectEventHandler;

      // should dispatch reflect event
      expect(reflectEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should update the current URL to have the query params from requestUrl
      // (except for those that are empty)
      // as the reflect-value attribute is set to true
      expect(window.location.search).toEqual('?foo=bar&xyz=123');
    });

    it('should allow for blocking the reflection of query params with event handlers', async () => {
      const expectedRequestUrl = '/path/to-src-value/?foo=bar&abc=&xyz=123';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      const reflectEventHandler = jest.fn((event) => {
        event.preventDefault();
      });

      document.addEventListener('w-swap:reflect', reflectEventHandler);

      formElement.setAttribute('data-w-swap-src-value', expectedRequestUrl);
      formElement.setAttribute('data-w-swap-reflect-value', 'true');

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch reflect event
      expect(reflectEventHandler).toHaveBeenCalledTimes(1);
      expect(reflectEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is set to false
      expect(window.location.search).toEqual('');

      document.removeEventListener('w-swap:reflect', reflectEventHandler);
    });

    it('should support replace with a url value provided via the Custom event detail', async () => {
      const expectedRequestUrl = '/path/to/url-in-event-detail/?q=alpha';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      formElement.dispatchEvent(
        new CustomEvent('custom:event', {
          bubbles: false,
          detail: { url: expectedRequestUrl },
        }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should support replace with a url value provided via an action param', async () => {
      const expectedRequestUrl = '/path/to/url-in-action-param/#hash';

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      formElement.setAttribute('data-w-swap-url-param', expectedRequestUrl);

      formElement.dispatchEvent(
        new CustomEvent('custom:event', { bubbles: false }),
      );

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expectedRequestUrl,
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('content').querySelectorAll('li'),
      ).toHaveLength(2);

      await flushPromises();

      // should NOT update the current URL
      expect(window.location.search).toEqual('');
    });
  });

  describe('performing a content update via actions on a controlled form using form values', () => {
    beforeEach(() => {
      // intentionally testing without target input (icon not needed & should work without this)

      document.body.innerHTML = /* html */ `
      <main>
      <form
        class="search-form"
        action="/path/to/form/action/"
        method="get"
        role="search"
        data-controller="w-swap"
        data-action="change->w-swap#submitLazy submit:prevent->w-swap#submitLazy"
        data-w-swap-target-value="#task-results"
      >
        <input id="search" type="text" name="q"/>
        <input name="type" type="hidden" value="some-type" />
        <input name="other" type="text" />
        <button type="submit">Submit</button>
      </form>
      <div id="task-results"></div>
      </main>
      `;

      window.history.replaceState(null, '', '?');
    });

    it('should allow for searching via a declared action on input changes', async () => {
      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      // Even if the attribute and the property use lowercase
      const formElement = document.querySelector('form');
      expect(formElement.getAttribute('method')).toEqual('get');
      expect(formElement.method).toEqual('get');

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=some-type&other=something+on+other',
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/form/action/?q=alpha&type=some-type&other=something+on+other',
        expect.objectContaining({
          // Should normalize the method name to uppercase and not send a body
          method: 'GET',
          body: undefined,
        }),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=some-type&other=something+on+other',
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('task-results').querySelectorAll('li').length,
      ).toBeTruthy();

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should support using the form method as the fetch request method', async () => {
      const input = document.getElementById('search');
      const formElement = document.querySelector('form');
      const expectedRequestUrl = '/custom/to-src-value/?with=param';

      formElement.setAttribute('data-w-swap-src-value', expectedRequestUrl);
      formElement.setAttribute('method', 'post');

      const results = getMockResults({ total: 5 });

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        // The form data should be serialized and sent as the body,
        // not as query params
        expectedRequestUrl,
        expect.objectContaining({
          headers: {
            'x-requested-with': 'XMLHttpRequest',
            'x-xsrf-token': 'potato',
          },
          method: 'POST',
          body: expect.any(FormData),
        }),
      );
      expect(
        Object.fromEntries(global.fetch.mock.lastCall[1].body.entries()),
      ).toEqual({
        // eslint-disable-next-line id-length
        q: 'alpha',
        type: 'some-type',
        other: 'something on other',
      });

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('task-results').querySelectorAll('li').length,
      ).toBeTruthy();

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should use the normalized method name and not send a body in a GET request', async () => {
      const input = document.getElementById('search');
      const formElement = document.querySelector('form');

      // Use a non-standard casing for the method
      formElement.setAttribute('method', 'Get');
      expect(formElement.getAttribute('method')).toEqual('Get');

      // The method property is an enum that always uses lowercase
      // https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#attr-fs-method
      expect(formElement.method).toEqual('get');

      const results = getMockResults({ total: 5 });

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      const expectedRequestUrl =
        '/path/to/form/action/?q=alpha&type=some-type&other=something+on+other';
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: expectedRequestUrl,
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        // The form data should be sent as query params, without the body
        expectedRequestUrl,
        expect.objectContaining({
          headers: {
            'x-requested-with': 'XMLHttpRequest',
            'x-xsrf-token': 'potato',
          },
          method: 'GET', // normalized method name should be in uppercase
          body: undefined,
        }),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: expectedRequestUrl,
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('task-results').querySelectorAll('li').length,
      ).toBeTruthy();

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should reflect the query params of the request URL if reflect-value is true', async () => {
      const formElement = document.querySelector('form');
      formElement.setAttribute('data-w-swap-reflect-value', 'true');

      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      document.querySelector('[name="type"]').value = '';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=&other=something+on+other',
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/form/action/?q=alpha&type=&other=something+on+other',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=&other=something+on+other',
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('task-results').querySelectorAll('li').length,
      ).toBeTruthy();

      await flushPromises();

      // should update the current URL to have the query params from requestUrl
      // (except for those that are empty)
      // as the reflect-value attribute is set to true
      expect(window.location.search).toEqual(
        '?q=alpha&other=something+on+other',
      );
    });

    it('should allow for blocking the reflection of query params with event handlers', async () => {
      const formElement = document.querySelector('form');
      formElement.setAttribute('data-w-swap-reflect-value', 'true');

      const reflectEventHandler = jest.fn((event) => {
        event.preventDefault();
      });

      document.addEventListener('w-swap:reflect', reflectEventHandler);

      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      document.querySelector('[name="type"]').value = '';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=&other=something+on+other',
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/form/action/?q=alpha&type=&other=something+on+other',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch reflect event
      expect(reflectEventHandler).toHaveBeenCalledTimes(1);
      expect(reflectEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=&other=something+on+other',
      });

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=&other=something+on+other',
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('task-results').querySelectorAll('li').length,
      ).toBeTruthy();

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is set to false
      expect(window.location.search).toEqual('');

      document.removeEventListener('w-swap:reflect', reflectEventHandler);
    });

    it('should allow for blocking the request with custom events', async () => {
      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const beginEventHandler = jest.fn((event) => {
        event.preventDefault();
      });

      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(results);

      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      input.value = 'alpha';
      document.querySelector('[name="other"]').value = 'something on other';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // search is debounced
      await Promise.resolve();

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl:
          '/path/to/form/action/?q=alpha&type=some-type&other=something+on+other',
      });

      expect(global.fetch).not.toHaveBeenCalled();

      document.removeEventListener('w-swap:begin', beginEventHandler);
    });
  });

  describe('performing a content update using HTML in JSON response', () => {
    let button;
    let results;
    const onErrorEvent = jest.fn();

    beforeEach(() => {
      document.body.innerHTML = `
      <main>
        <form
          action="/path/to/editing-sessions/"
          method="get"
          data-controller="w-swap"
          data-action="submit->w-swap#submitLazy:prevent"
          data-w-swap-target-value="#editing-sessions"
          data-w-swap-json-path-value="nested.data.results"
        >
          <input name="title" type="text"/>
          <input name="type" type="hidden" value="some-type" />
          <button type="submit">Submit<button>
        </form>
        <div id="editing-sessions"></div>
      </main>
      `;

      button = document.querySelector('button');
      results = getMockResults({ total: 5 });
    });

    const expectErrorHandled = async () => {
      expect(window.location.search).toEqual('');
      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      button.click();

      jest.runAllTimers(); // update is debounced

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      expect(onErrorEvent).not.toHaveBeenCalled();

      await Promise.resolve(); // trigger next rendering

      await flushPromises(); // resolve all promises

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenLastCalledWith(
        'Error fetching %s',
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Error),
      );
      // eslint-disable-next-line no-console
      expect(console.error.mock.lastCall[2]).toEqual(
        expect.objectContaining({
          message:
            'Unable to parse as JSON at path "nested.data.results" to a string',
        }),
      );

      // should not update any HTML
      expect(document.getElementById('editing-sessions').innerHTML).toEqual('');

      // should have dispatched a custom event for the error
      expect(onErrorEvent).toHaveBeenCalledTimes(1);
      expect(onErrorEvent.mock.calls[0][0].detail).toEqual({
        error: expect.any(Error),
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      await Promise.resolve(); // trigger next rendering
    };

    it('should update the target element with the HTML content from the JSON response', async () => {
      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const jsonEventHandler = new Promise((resolve) => {
        document.addEventListener('w-swap:json', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results } } }),
      );

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      button.click();

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // submit is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      await Promise.resolve();

      const jsonEvent = await jsonEventHandler;

      // should dispatch json event
      expect(jsonEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
        data: expect.objectContaining({ nested: { data: { results } } }),
      });

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
        results: expect.any(String),
      });

      // should update HTML
      expect(
        document.getElementById('editing-sessions').querySelectorAll('li')
          .length,
      ).toBeTruthy();

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should handle non-JSON response gracefully', async () => {
      document.addEventListener('w-swap:error', onErrorEvent);

      const jsonEventHandler = jest.fn();
      document.addEventListener('w-swap:json', jsonEventHandler);

      fetch.mockResponseSuccessText('<div><p>Some HTML content</p></div>');

      await expectErrorHandled();

      // should not dispatch json event
      expect(jsonEventHandler).not.toHaveBeenCalled();
    });

    it('should handle non-existing key gracefully', async () => {
      document.addEventListener('w-swap:error', onErrorEvent);

      const jsonEventHandler = jest.fn();
      document.addEventListener('w-swap:json', jsonEventHandler);

      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { differentKey: results } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { differentKey: results } },
            }),
          },
        }),
      );
    });

    it('should handle non-string values gracefully', async () => {
      document.addEventListener('w-swap:error', onErrorEvent);
      const jsonEventHandler = jest.fn();
      document.addEventListener('w-swap:json', jsonEventHandler);

      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results: 123 } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { results: 123 } },
            }),
          },
        }),
      );

      jest.clearAllMocks();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results: true } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { results: true } },
            }),
          },
        }),
      );

      jest.clearAllMocks();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results: null } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { results: null } },
            }),
          },
        }),
      );

      jest.clearAllMocks();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results: { some: 'object' } } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { results: { some: 'object' } } },
            }),
          },
        }),
      );

      jest.clearAllMocks();
      fetch.mockResponseSuccessJSON(
        JSON.stringify({ nested: { data: { results: [1, false, 'hello'] } } }),
      );

      await expectErrorHandled();

      // should still dispatch json event
      expect(jsonEventHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: {
            requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
            data: expect.objectContaining({
              nested: { data: { results: [1, false, 'hello'] } },
            }),
          },
        }),
      );
    });
  });

  describe('deferring the content update until the focus is out of the target container', () => {
    const getMockResultsWithButtons = (total) =>
      getMockResults({ total }) +
      `<button id="button1">Focusable 1</button><button id="button2">Focusable 2</button>`;

    beforeEach(() => {
      document.body.innerHTML = /* html */ `
      <main>
        <svg class="icon icon-breadcrumb-expand" aria-hidden="true">
          <use href="#icon-breadcrumb-expand"></use>
        </svg>
        <form
          action="/path/to/editing-sessions/"
          method="get"
          data-controller="w-swap"
          data-action="submit->w-swap#submitLazy:prevent"
          data-w-swap-defer-value="true"
          data-w-swap-target-value="#editing-sessions"
        >
          <input name="title" type="text"/>
          <input name="type" type="hidden" value="some-type" />
          <button id="submit" type="submit">Submit</button>
        </form>
        <div id="editing-sessions">
          <div>
            <button id="button1">Focusable 1</button>
            <button id="button2">Focusable 2</button>
          </div>
        </div>
      </main>
      `;
    });

    it('should wait until the target loses focus and continue execution immediately after', async () => {
      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(getMockResultsWithButtons(5));

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      document.getElementById('submit').click();

      // focus on an element inside the target container
      document.getElementById('button1').focus();

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // submit is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      // visual loading state should not be shown
      await Promise.resolve(); // trigger next rendering
      const icon = document.querySelector('.icon use');
      const target = document.getElementById('editing-sessions');
      expect(icon.getAttribute('href')).toEqual('#icon-breadcrumb-expand');
      expect(target.getAttribute('aria-busy')).toBeNull();

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      // simulate the request completing
      await Promise.resolve();

      // should not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      await flushPromises();

      // should still not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // switch focus to a different element but still inside the target container
      document.getElementById('button2').focus();

      await flushPromises();

      // should still not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // switch focus to an element outside the target container
      document.getElementById('submit').focus();

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
        results: expect.any(String),
      });

      // should update HTML
      expect(target.querySelectorAll('li').length).toEqual(5);

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should not wait until the target loses focus if defer value is set to false', async () => {
      // unset the defer value (default is false)
      const form = document.querySelector('form');
      form.removeAttribute('data-w-swap-defer-value');

      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(getMockResultsWithButtons(5));

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      document.getElementById('submit').click();

      // focus on an element inside the target container
      document.getElementById('button1').focus();

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // submit is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      // visual loading state should be active
      await Promise.resolve(); // trigger next rendering
      const icon = document.querySelector('.icon use');
      const target = document.getElementById('editing-sessions');
      expect(icon.getAttribute('href')).toEqual('#icon-spinner');
      expect(target.getAttribute('aria-busy')).toEqual('true');

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      // simulate the request completing
      await Promise.resolve();

      // should not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      await flushPromises();

      // if the deferred write happens (which should not), the test will
      // time out because the focus is still inside the target container
      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
        results: expect.any(String),
      });

      // should update HTML
      expect(target.querySelectorAll('li').length).toEqual(5);

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should wait until all tooltips are gone and continue execution immediately after', async () => {
      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', resolve);
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(getMockResultsWithButtons(5));

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      document.getElementById('submit').click();

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // submit is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      // visual loading state should not be shown
      await Promise.resolve(); // trigger next rendering
      const icon = document.querySelector('.icon use');
      const target = document.getElementById('editing-sessions');
      expect(icon.getAttribute('href')).toEqual('#icon-breadcrumb-expand');
      expect(target.getAttribute('aria-busy')).toBeNull();

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      // simulate the request completing
      await Promise.resolve();

      // should not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // simulate a popup being shown
      const popup = document.createElement('div');
      popup.setAttribute('aria-expanded', 'true');
      target.appendChild(popup);

      await flushPromises();

      // should still not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // hide the popup and replace it with a tooltip
      popup.setAttribute('aria-expanded', 'false');
      const elementWithTooltip = document.createElement('button');
      elementWithTooltip.setAttribute('aria-describedby', 'tippy-1');
      document
        .getElementById('editing-sessions')
        .appendChild(elementWithTooltip);
      const tippy = document.createElement('div');
      tippy.id = 'tippy-1';
      document.body.appendChild(tippy);

      await flushPromises();

      // should still not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // hide the tooltip
      elementWithTooltip.removeAttribute('aria-describedby');

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
        results: expect.any(String),
      });

      // should update HTML
      expect(target.querySelectorAll('li').length).toEqual(5);

      await flushPromises();

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });

    it('should write immediately if there is a deferred write but we no longer need to defer', async () => {
      const successEvents = [];
      const onSuccess = new Promise((resolve) => {
        document.addEventListener('w-swap:success', (event) => {
          successEvents.push(event);
          resolve(event);
        });
      });

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockResponseSuccessText(getMockResultsWithButtons(5));

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();

      document.getElementById('submit').click();

      // focus on an element inside the target container
      document.getElementById('button1').focus();

      expect(beginEventHandler).not.toHaveBeenCalled();

      jest.runAllTimers(); // submit is debounced

      // should fire a begin event before the request is made
      expect(beginEventHandler).toHaveBeenCalledTimes(1);
      expect(beginEventHandler.mock.calls[0][0].detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=&type=some-type',
      });

      // visual loading state should not be shown
      await Promise.resolve(); // trigger next rendering
      const icon = document.querySelector('.icon use');
      const target = document.getElementById('editing-sessions');
      expect(icon.getAttribute('href')).toEqual('#icon-breadcrumb-expand');
      expect(target.getAttribute('aria-busy')).toBeNull();

      expect(handleError).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=&type=some-type',
        expect.any(Object),
      );

      // simulate the request completing
      await Promise.resolve();

      // should not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      await flushPromises();

      // should still not update HTML just yet
      expect(target.querySelectorAll('li').length).toEqual(0);

      // instead of switching the focus outside, we set the defer value
      // to false, so we can test the case where a new update is not deferred but
      // there is a deferred write and the focus is still inside the target container
      const form = document.querySelector('form');
      form.setAttribute('data-w-swap-defer-value', 'false');

      // change the input so we can trigger a new request with a different URL to check
      document.querySelector('input[name="title"]').value = 'newvalue';

      // submit the form again
      form.submit();
      fetch.mockResponseSuccessText(getMockResultsWithButtons(8));
      jest.runAllTimers();
      await flushPromises();

      expect(global.fetch).toHaveBeenCalledWith(
        '/path/to/editing-sessions/?title=newvalue&type=some-type',
        expect.any(Object),
      );

      const successEvent = await onSuccess;

      // should dispatch success event
      expect(successEvent.detail).toEqual({
        requestUrl: '/path/to/editing-sessions/?title=newvalue&type=some-type',
        results: expect.any(String),
      });

      // should skip the deferred write and instead write the last request's response (8 items)
      expect(target.querySelectorAll('li').length).toEqual(8);

      await flushPromises();

      // should still use the last request's response instead of running the deferred write
      expect(target.querySelectorAll('li').length).toEqual(8);

      // Simulate triggering the unlikely edge case of the focusout event being triggered,
      // with no deferred writes left, which theoretically could only happen if the
      // defer value was changed to false at midpoint like in this test case.
      // We need to regain focus on an element in the target container first,
      // because the previous element that was focused is no longer in the DOM.
      document.getElementById('button1').focus();
      // then we focus out
      document.getElementById('submit').focus();

      jest.runAllTimers();
      await flushPromises();

      // should still use the last request's response instead of running the deferred write
      expect(target.querySelectorAll('li').length).toEqual(8);

      // the success event should be dispatched only once as the deferred write was skipped
      expect(successEvents).toHaveLength(1);
      expect(successEvents[0].detail.requestUrl).toEqual(
        '/path/to/editing-sessions/?title=newvalue&type=some-type',
      );

      // should NOT update the current URL
      // as the reflect-value attribute is not set
      expect(window.location.search).toEqual('');
    });
  });
});
