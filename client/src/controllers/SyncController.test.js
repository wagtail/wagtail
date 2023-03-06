import { Application } from '@hotwired/stimulus';
import { SyncController } from './SyncController';

jest.useFakeTimers();

describe('SyncController', () => {
  let application;

  describe('basic sync between two fields', () => {
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
          data-action="change->w-sync#apply cut->w-sync#clear custom:event->w-sync#ping"
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
        value: '2025-05-05',
      });
    });

    it('should allow the sync field to clear the value of the target element', () => {
      const changeListener = jest.fn();
      document
        .getElementById('title')
        .addEventListener('change', changeListener);

      expect(document.getElementById('title').value).toEqual('2025-05-05');
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
      expect(document.getElementById('title').value).toEqual('');

      jest.runAllTimers();
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
      expect(document.getElementById('title').value).toEqual('2025-05-05');
      expect(changeListener).toHaveBeenCalledTimes(1);

      jest.runAllTimers();
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
});
