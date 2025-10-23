import $ from 'jquery';

import { setImmediate } from 'timers';
import { Application } from '@hotwired/stimulus';
import { TagController } from './TagController';

window.$ = $;

jest.useFakeTimers();

const flushPromises = () => new Promise(setImmediate);

describe('TagController', () => {
  let application;
  let element;

  const tagitMock = jest.fn(function innerFunction() {
    element = this;
  });

  window.$.fn.tagit = tagitMock;

  element = null;

  beforeAll(() => {
    application = Application.start();
    application.register('w-tag', TagController);
    application.handleError = jest.fn();
  });

  beforeEach(() => {
    element = null;
    jest.clearAllMocks();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve([]),
      }),
    );
  });

  afterEach(async () => {
    await flushPromises();
    jest.restoreAllMocks();
  });

  it('should attach the jQuery tagit to the controlled element', async () => {
    document.body.innerHTML = `
  <form id="form">
    <input
      id="id_tags"
      type="text"
      name="tags"
      data-controller="w-tag"
      data-action="example:event->w-tag#clear"
      data-w-tag-options-value="{&quot;allowSpaces&quot;:true,&quot;tagLimit&quot;:10}"
      data-w-tag-url-value="/admin/tag-autocomplete/"
    >
  </form>`;

    expect(tagitMock).not.toHaveBeenCalled();

    await flushPromises();

    expect(tagitMock).toHaveBeenCalledWith({
      allowSpaces: true,
      autocomplete: { source: expect.any(Function) },
      preprocessTag: expect.any(Function),
      tagLimit: 10,
    });

    expect(element[0]).toEqual(document.getElementById('id_tags'));

    // check the supplied preprocessTag function
    const [{ preprocessTag }] = tagitMock.mock.calls[0];

    expect(preprocessTag).toBeInstanceOf(Function);

    expect(preprocessTag()).toEqual();
    expect(preprocessTag('"flat white"')).toEqual(`"flat white"`);
    expect(preprocessTag("'long black'")).toEqual(`"'long black'"`);
    expect(preprocessTag('caffe latte')).toEqual(`"caffe latte"`);

    // check the custom clear behavior
    document
      .getElementById('id_tags')
      .dispatchEvent(new CustomEvent('example:event'));

    await flushPromises();

    expect(tagitMock).toHaveBeenCalledWith('removeAll');
  });

  describe('autocomplete', () => {
    let autocompleteSource;

    beforeAll(async () => {
      document.body.innerHTML = `
      <form id="form">
        <input
          id="id_tags"
          type="text"
          name="tags"
          data-controller="w-tag"
          data-action="example:event->w-tag#clear"
          data-w-tag-delay-value="300"
          data-w-tag-options-value='${JSON.stringify({
            allowSpaces: true,
            tagLimit: 10,
          })}'
          data-w-tag-url-value="/admin/tag-autocomplete/"
        >
      </form>`;

      await flushPromises();

      // get last mock call
      autocompleteSource =
        tagitMock.mock.calls[tagitMock.mock.calls.length - 1][0].autocomplete
          .source;
    });

    it('should handle a successful fetch response', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          json: () => Promise.resolve(['tag1', 'tag2', 'tag3']),
        }),
      );

      expect(autocompleteSource).toBeInstanceOf(Function);

      const result = await new Promise((resolve) => {
        autocompleteSource({ term: 'tag' }, resolve);
        jest.runAllTimers();
      });

      expect(result).toEqual(['tag1', 'tag2', 'tag3']);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/admin/tag-autocomplete/?term=tag'),
        {
          headers: { Accept: 'application/json' },
          method: 'GET',
          signal: expect.any(AbortSignal),
        },
      );
    });

    it('should handle empty term gracefully', async () => {
      const result = await new Promise((resolve) => {
        autocompleteSource({ term: '' }, resolve);
        jest.runAllTimers();
      });
      expect(result).toEqual([]);
    });

    it('should handle an empty fetch response', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          json: () => Promise.resolve([]),
        }),
      );

      expect(autocompleteSource).toBeInstanceOf(Function);

      const result = await new Promise((resolve) => {
        autocompleteSource({ term: 'nonexistent' }, resolve);
        jest.runAllTimers();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost/admin/tag-autocomplete/?term=nonexistent',
        expect.any(Object),
      );

      expect(result).toEqual([]);
    });

    it('should handle fetch errors gracefully', async () => {
      global.fetch = jest.fn(() => Promise.reject(new Error('Fetch error')));

      expect(application.handleError).not.toHaveBeenCalled();
      expect(autocompleteSource).toBeInstanceOf(Function);

      const result = await new Promise((resolve) => {
        autocompleteSource({ term: 'error' }, resolve);
        jest.runAllTimers();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost/admin/tag-autocomplete/?term=error',
        expect.any(Object),
      );

      // check we returned an empty array, even with an error
      expect(result).toEqual([]);

      // check the error gets handed to Stimulus
      expect(application.handleError).toHaveBeenCalledWith(
        new Error('Fetch error'),
        'Network or API error during autocomplete request.',
        { term: 'error', url: '/admin/tag-autocomplete/' },
      );
    });

    it('should debounce requests to the tag endpoint', async () => {
      // mocking a slow fetch
      global.fetch = jest.fn(
        () =>
          new Promise((resolve) => {
            window.setTimeout(resolve, 300);
          }),
      );

      expect(autocompleteSource).toBeInstanceOf(Function);

      const response = jest.fn();

      // First request
      autocompleteSource({ term: 'test1' }, response);
      jest.advanceTimersByTime(100);

      // Second request during debounce window
      autocompleteSource({ term: 'test2' }, response);
      jest.advanceTimersByTime(100);

      // Third request during debounce window
      autocompleteSource({ term: 'test3' }, response);
      jest.advanceTimersByTime(50);

      await jest.runAllTimersAsync();

      expect(fetch).toHaveBeenCalledTimes(1);

      expect(fetch).toHaveBeenCalledWith(
        // only the most recent request should be made
        expect.stringContaining('/admin/tag-autocomplete/?term=test3'),
        expect.any(Object),
      );

      expect(response).toHaveBeenCalledTimes(1);
      expect(response).toHaveBeenCalledWith([]);
    });

    it('should allow new requests to to be made after the debounce window & abort in-flight', async () => {
      // mock a slow fetch the first time but fast the second time
      global.fetch = jest
        .fn()
        .mockImplementationOnce(
          () =>
            new Promise((resolve) => {
              window.setTimeout(
                () =>
                  resolve({ json: () => Promise.resolve(['slow IGNORED']) }),
                600,
              );
            }),
        )
        .mockImplementationOnce(
          () =>
            new Promise((resolve) => {
              window.setTimeout(
                () => resolve({ json: () => Promise.resolve(['slow cooked']) }),
                50,
              );
            }),
        );

      expect(autocompleteSource).toBeInstanceOf(Function);

      const response = jest.fn();

      // First request
      autocompleteSource({ term: 's' }, response);
      jest.advanceTimersByTime(300);

      // Second request after previous debounce window
      autocompleteSource({ term: 'slow' }, response);

      await jest.runAllTimersAsync();

      expect(fetch).toHaveBeenCalledTimes(2);

      expect(fetch).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('/admin/tag-autocomplete/?term=s'),
        expect.any(Object),
      );

      expect(fetch).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('/admin/tag-autocomplete/?term=slow'),
        expect.any(Object),
      );

      expect(application.handleError).not.toHaveBeenCalled();

      expect(response).toHaveBeenCalledTimes(2);
    });
  });
});
