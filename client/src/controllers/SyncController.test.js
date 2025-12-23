import { Application } from '@hotwired/stimulus';
import { SyncController } from './SyncController';

import { range } from '../utils/range';

jest.useFakeTimers();
jest.spyOn(global, 'setTimeout');

describe('SyncController', () => {
  let application;

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('basic sync between two fields', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
      <section>
        <input type="text" name="title" id="title" />
        <input
          type="date"
          id="event-date"
          name="event-date"
          value="2025-07-22"
          data-controller="w-sync"
          data-action="change->w-sync#apply keyup->w-sync#apply cut->w-sync#clear custom:event->w-sync#ping"
          data-w-sync-target-value="#title"
        />
      </section>`;

      application = Application.start();
    });

    afterAll(() => {
      document.body.innerHTML = '';
      jest.clearAllMocks();
      jest.clearAllTimers();
    });

    it('should dispatch a start event on targeted element', () => {
      const startListener = jest.fn();
      document
        .getElementById('title')
        .addEventListener('w-sync:start', startListener);

      expect(startListener).not.toHaveBeenCalled();

      application.register('w-sync', SyncController);

      expect(startListener).toHaveBeenCalledTimes(1);

      expect(startListener.mock.calls[0][0].detail).toEqual({
        element: document.getElementById('event-date'),
        value: '2025-07-22',
      });
    });

    it('should allow the sync field to apply its value to the target element', () => {
      const changeListener = jest.fn();
      document
        .getElementById('title')
        .addEventListener('change', changeListener);

      expect(document.getElementById('title').value).toEqual('');
      expect(changeListener).not.toHaveBeenCalled();

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');

      dateInput.value = '2025-05-05';
      dateInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('title').value).toEqual('2025-05-05');
      expect(changeListener).toHaveBeenCalledTimes(1);
    });

    it('should allow for a simple ping against the target field that bubbles', () => {
      const pingListener = jest.fn();
      document.addEventListener('w-sync:ping', pingListener);

      expect(pingListener).not.toHaveBeenCalled();

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');

      dateInput.dispatchEvent(new CustomEvent('custom:event'));

      expect(pingListener).toHaveBeenCalledTimes(1);
      const event = pingListener.mock.calls[0][0];

      expect(event.target).toEqual(document.getElementById('title'));

      expect(event.detail).toEqual({
        element: document.getElementById('event-date'),
        value: '2025-07-22',
      });
    });

    it('should allow the sync field to clear the value of the target element', () => {
      const changeListener = jest.fn();
      document
        .getElementById('title')
        .addEventListener('change', changeListener);

      const titleElement = document.getElementById('title');
      titleElement.setAttribute('value', 'initial title');
      expect(changeListener).not.toHaveBeenCalled();

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');

      dateInput.dispatchEvent(new Event('cut'));

      jest.runAllTimers();

      expect(document.getElementById('title').value).toEqual('');
      expect(changeListener).toHaveBeenCalledTimes(1);
    });

    it('should allow for no change events to be dispatched', () => {
      const dateInput = document.getElementById('event-date');
      dateInput.setAttribute('data-w-sync-quiet-value', 'true');

      application.register('w-sync', SyncController);

      dateInput.value = '2025-05-05';
      dateInput.dispatchEvent(new Event('change'));

      expect(dateInput.getAttribute('data-w-sync-quiet-value')).toBeTruthy();
      expect(document.getElementById('title').value).toEqual('');

      dateInput.value = '2025-05-05';
      dateInput.dispatchEvent(new Event('cut'));

      expect(document.getElementById('title').value).toEqual('');
    });

    it('should debounce multiple consecutive calls to apply by default', () => {
      const titleInput = document.getElementById('title');
      const dateInput = document.getElementById('event-date');

      const changeListener = jest.fn();

      titleInput.addEventListener('change', changeListener);

      dateInput.value = '2027-10-14';

      application.register('w-sync', SyncController);

      range(0, 8).forEach(() => {
        dateInput.dispatchEvent(new Event('keyup'));
        jest.advanceTimersByTime(5);
      });

      expect(changeListener).not.toHaveBeenCalled();
      expect(titleInput.value).toEqual('');

      jest.advanceTimersByTime(50); // not yet reaching the 100ms debounce value

      expect(changeListener).not.toHaveBeenCalled();
      expect(titleInput.value).toEqual('');

      jest.advanceTimersByTime(50); // pass the 100ms debounce value

      // keyup run multiple times, only one change event should occur
      expect(titleInput.value).toEqual('2027-10-14');
      expect(changeListener).toHaveBeenCalledTimes(1);

      // adjust the delay via a data attribute
      dateInput.setAttribute('data-w-sync-delay-value', '500');

      range(0, 8).forEach(() => {
        dateInput.dispatchEvent(new Event('keyup'));
        jest.advanceTimersByTime(5);
      });

      jest.advanceTimersByTime(300); // not yet reaching the custom debounce value
      expect(changeListener).toHaveBeenCalledTimes(1);

      jest.advanceTimersByTime(295); // passing the custom debounce value
      expect(changeListener).toHaveBeenCalledTimes(2);
    });
  });

  describe('delayed sync between two fields', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
      <section>
        <input type="text" name="title" id="title" />
        <input
          type="date"
          id="event-date"
          name="event-date"
          value="2025-07-22"
          data-controller="w-sync"
          data-action="change->w-sync#apply cut->w-sync#clear"
          data-w-sync-target-value="#title"
          data-w-sync-delay-value="500"
        />
      </section>`;

      application = Application.start();
    });

    it('should delay the update on change based on the set value', () => {
      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');
      dateInput.value = '2025-05-05';

      dateInput.dispatchEvent(new Event('cut'));

      jest.advanceTimersByTime(500);

      expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 500);

      jest.runAllTimers();

      expect(document.getElementById('title').value).toEqual('');
    });

    it('should delay the update on apply based on the set value', () => {
      const changeListener = jest.fn();
      document
        .getElementById('title')
        .addEventListener('change', changeListener);

      expect(document.getElementById('title').value).toEqual('');
      expect(changeListener).not.toHaveBeenCalled();

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');

      dateInput.value = '2025-05-05';
      dateInput.dispatchEvent(new Event('change'));

      jest.advanceTimersByTime(500);

      expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 500);

      jest.runAllTimers();

      expect(document.getElementById('title').value).toEqual('2025-05-05');
      expect(changeListener).toHaveBeenCalledTimes(1);
    });
  });

  describe('ability for the sync to be disabled between two fields', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
      <section>
        <input type="text" name="title" id="title" value="keep me"/>
        <input
          type="date"
          id="event-date"
          name="event-date"
          value="2025-07-22"
          data-controller="w-sync"
          data-action="change->w-sync#apply cut->w-sync#clear focus->w-sync#check"
          data-w-sync-target-value="#title"
        />
      </section>`;

      application = Application.start();
    });

    it('should allow for the target element to block syncing at the start', () => {
      const titleElement = document.getElementById('title');

      expect(titleElement.value).toEqual('keep me');

      titleElement.addEventListener('w-sync:start', (event) => {
        event.preventDefault();
      });

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');

      dateInput.value = '2025-05-05';
      dateInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(titleElement.value).toEqual('keep me');
      expect(dateInput.getAttribute('data-w-sync-disabled-value')).toBeTruthy();
    });

    it('should allow for the target element to block syncing with the check approach', () => {
      const titleElement = document.getElementById('title');

      expect(titleElement.value).toEqual('keep me');

      titleElement.addEventListener('w-sync:check', (event) => {
        event.preventDefault();
      });

      application.register('w-sync', SyncController);

      const dateInput = document.getElementById('event-date');
      dateInput.setAttribute('data-w-sync-disabled-value', '');

      dateInput.value = '2025-05-05';

      dateInput.dispatchEvent(new Event('focus'));
      dateInput.dispatchEvent(new Event('cut'));

      jest.runAllTimers();

      expect(titleElement.value).toEqual('keep me');
      expect(dateInput.getAttribute('data-w-sync-disabled-value')).toBeTruthy();
    });
  });

  describe('ability to use sync for other field behavior', () => {
    beforeAll(() => {
      application?.stop();
    });

    it('should allow the sync clear method to be used on a button to clear target fields', async () => {
      document.body.innerHTML = `
      <section>
        <input type="text" name="title" id="title" value="a title field"/>
        <button
          type="button"
          id="clear"
          data-controller="w-sync"
          data-action="w-sync#clear"
          data-w-sync-target-value="#title"
        >Clear</button>
      </section>`;

      application = Application.start();

      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('title').value).toEqual('a title field');

      document.getElementById('clear').click();

      expect(document.getElementById('title').innerHTML).toEqual('');
    });

    it('should allow the sync apply method to accept a param instead of the element value', async () => {
      document.body.innerHTML = `
      <section>
        <select name="pets" id="pet-select">
          <option value="dog">Dog</option>
          <option value="cat">Cat</option>
          <option value="pikachu">Pikachu</option>
          <option value="goldfish">Goldfish</option>
        </select>
        <button
          type="button"
          id="choose"
          data-controller="w-sync"
          data-action="w-sync#apply"
          data-w-sync-apply-param="pikachu"
          data-w-sync-target-value="#pet-select"
        >Choose Pikachu</button>
      </section>`;

      application = Application.start();

      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('pet-select').value).toEqual('dog');

      document.getElementById('choose').dispatchEvent(new Event('click'));

      jest.runAllTimers();

      expect(document.getElementById('pet-select').value).toEqual('pikachu');
    });
  });

  describe('value normalization', () => {
    beforeAll(() => {
      application?.stop();
    });

    it('should return the value as-is by default', async () => {
      document.body.innerHTML = /* html */ `
        <section>
          <input
            type="text"
            name="title"
            maxlength="255"
            required
            id="id_title"
          />
          <input
            type="text"
            name="other"
            data-controller="w-sync"
            data-action="change->w-sync#apply"
            data-w-sync-normalize-value="true"
            data-w-sync-target-value="#id_title"
            required
            id="id_other"
          />
        </section>
      `;

      application = Application.start();

      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('id_title').value).toEqual('');

      const otherInput = document.getElementById('id_other');
      otherInput.value = 'something';
      otherInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('id_title').value).toEqual('something');
    });

    it('should normalize file input values by removing fakepath and extension', async () => {
      document.body.innerHTML = /* html */ `
        <section>
          <input
            type="text"
            name="title"
            maxlength="255"
            required
            id="id_title"
          />
          <input
            type="file"
            name="file"
            data-controller="w-sync"
            data-action="change->w-sync#apply"
            data-w-sync-normalize-value="true"
            data-w-sync-target-value="#id_title"
            required
            id="id_file"
          />
        </section>
      `;

      application = Application.start();

      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('id_title').value).toEqual('');

      const fileInput = document.getElementById('id_file');

      // JSDOM does not support setting the value of a file input directly.
      // https://github.com/jsdom/jsdom/issues/1272
      Object.defineProperty(fileInput, 'value', {
        value: 'C:\\fakepath\\my image.png',
      });
      fileInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('id_title').value).toEqual('my image');
    });
  });

  describe('legacy title generation customization event handling', () => {
    let eventListener;

    beforeEach(() => {
      application?.stop();
      document.body.innerHTML = /* html */ `
        <form>
          <input
            type="text"
            name="title"
            maxlength="255"
            required
            id="id_title"
          />
          <input
            type="file"
            name="file"
            data-controller="w-sync"
            data-action="change->w-sync#apply"
            data-w-sync-bubbles-param="true"
            data-w-sync-name-value="wagtail:documents-upload"
            data-w-sync-normalize-value="true"
            data-w-sync-target-value="#id_title"
            required
            id="id_file"
          />
        </form>
      `;
    });

    afterEach(() => {
      document.removeEventListener('wagtail:documents-upload', eventListener);
    });

    it('should not replace the title if there is an existing value', async () => {
      eventListener = jest.fn();

      document.addEventListener('wagtail:documents-upload', eventListener);

      application = Application.start();
      application.register('w-sync', SyncController);

      await Promise.resolve();

      const titleInput = document.getElementById('id_title');
      titleInput.value = 'existing title';

      expect(titleInput.value).toEqual('existing title');

      const fileInput = document.getElementById('id_file');

      // JSDOM does not support setting the value of a file input directly.
      // https://github.com/jsdom/jsdom/issues/1272
      Object.defineProperty(fileInput, 'value', {
        value: 'C:\\fakepath\\my document.pdf',
      });
      fileInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('id_title').value).toEqual(
        'existing title',
      );
      expect(eventListener).not.toHaveBeenCalled();
    });

    it('should dispatch legacy event with mutable data.title property', async () => {
      eventListener = (event) => {
        expect(event.target).toBeInstanceOf(HTMLFormElement);
        expect(event.detail.data.title).toEqual('my document');
        expect(event.detail.maxTitleLength).toEqual(255);
        expect(event.detail.filename).toEqual('my document.pdf');
        const extension = (event.detail.filename.match(
          /\.([^.]*?)(?=\?|#|$)/,
        ) || [''])[1];
        const newTitle = `(${extension.toUpperCase()}) ${event.detail.data.title || ''}`;
        event.detail.data.title = newTitle;
      };

      document.addEventListener('wagtail:documents-upload', eventListener);

      application = Application.start();
      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('id_title').value).toEqual('');

      const fileInput = document.getElementById('id_file');

      // JSDOM does not support setting the value of a file input directly.
      // https://github.com/jsdom/jsdom/issues/1272
      Object.defineProperty(fileInput, 'value', {
        value: 'C:\\fakepath\\my document.pdf',
      });
      fileInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('id_title').value).toEqual(
        '(PDF) my document',
      );
    });

    it('should allow cancelling the automatic title generation', async () => {
      eventListener = (event) => {
        expect(event.target).toBeInstanceOf(HTMLFormElement);
        expect(event.detail.data.title).toEqual('my image');
        expect(event.detail.maxTitleLength).toBeNull();
        expect(event.detail.filename).toEqual('my image.png');
        event.preventDefault();
      };

      document.addEventListener('wagtail:images-upload', eventListener);

      const fileInput = document.getElementById('id_file');
      const titleInput = document.getElementById('id_title');
      fileInput.setAttribute('data-w-sync-name-value', 'wagtail:images-upload');
      titleInput.removeAttribute('maxlength');

      application = Application.start();
      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(titleInput.value).toEqual('');

      // JSDOM does not support setting the value of a file input directly.
      // https://github.com/jsdom/jsdom/issues/1272
      Object.defineProperty(fileInput, 'value', {
        value: 'C:\\fakepath\\my image.png',
      });
      fileInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(titleInput.value).toEqual('');
    });

    it('should ignore unknown legacy events', async () => {
      eventListener = jest.fn();
      const fileInput = document.getElementById('id_file');
      fileInput.setAttribute('data-w-sync-name-value', 'unknown:event');

      document.addEventListener('unknown:event', eventListener);

      application = Application.start();
      application.register('w-sync', SyncController);

      await Promise.resolve();

      expect(document.getElementById('id_title').value).toEqual('');

      // JSDOM does not support setting the value of a file input directly.
      Object.defineProperty(fileInput, 'value', {
        value: 'C:\\fakepath\\my document.pdf',
      });
      fileInput.dispatchEvent(new Event('change'));

      jest.runAllTimers();

      expect(document.getElementById('id_title').value).toEqual('my document');
      expect(eventListener).not.toHaveBeenCalled();
    });
  });
});
