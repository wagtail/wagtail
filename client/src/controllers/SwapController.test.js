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

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );

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

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
        }),
      );

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
        'Error fetching /admin/images/results/?q=alpha',
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

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );

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

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );

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

  describe('performing a content update via actions on a controlled form using form values', () => {
    let beginEventHandler;
    let formElement;
    let onSuccess;
    const results = getMockResults({ total: 2 });

    beforeEach(() => {
      document.body.innerHTML = `
      <main>
      <form
        id="form"
        action="/path/to/form/action/"
        method="get"
        data-controller="w-swap"
        data-action="custom:event->w-swap#replaceLazy submit:prevent->w-swap#replace"
        data-w-swap-target-value="#content"
      >
        <button type="submit">Submit<button>
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

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );
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
      ).toHaveLength(5);

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

      document.body.innerHTML = `
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
        <button type="submit">Submit<button>
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

      const beginEventHandler = jest.fn();
      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );

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
        expect.any(Object),
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
      expect(window.location.search).toEqual('');
    });

    it('should allow for blocking the request with custom events', async () => {
      const input = document.getElementById('search');

      const results = getMockResults({ total: 5 });

      const beginEventHandler = jest.fn((event) => {
        event.preventDefault();
      });

      document.addEventListener('w-swap:begin', beginEventHandler);

      fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(results),
        }),
      );

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
});
