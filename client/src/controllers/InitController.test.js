import { Application } from '@hotwired/stimulus';
import { InitController } from './InitController';

jest.useFakeTimers();

describe('InitController', () => {
  let application;

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('default behavior', () => {
    const handleEvent = jest.fn();
    document.addEventListener('w-init:ready', handleEvent);

    beforeAll(() => {
      jest.clearAllMocks();

      application?.stop();
      document.body.innerHTML = `
        <div
          id="test"
          class="hide-me"
          data-controller="w-init"
          data-w-init-remove-class="hide-me"
          data-w-init-ready-class="ready"
        >
          Test body
        </div>
      `;

      application = Application.start();
    });

    it('should add a "ready" class and remove specified classes after connection', async () => {
      const testDiv = document.getElementById('test');

      application.register('w-init', InitController);
      expect(testDiv.classList).toContain('hide-me');
      expect(testDiv.classList).not.toContain('ready');

      await Promise.resolve(); // no delay, just wait for the next tick

      expect(testDiv.classList).toContain('ready');
      expect(testDiv.classList).not.toContain('hide-me');
    });

    it('should remove the controller correctly', () => {
      const testDiv = document.getElementById('test');

      expect(handleEvent).toHaveBeenCalledTimes(1);
      expect(testDiv.getAttribute('data-controller')).toBeNull();
      expect({ ...testDiv.dataset }).toEqual({});
    });
  });

  describe('with a delay', () => {
    const handleEvent = jest.fn();
    document.addEventListener('w-init:ready', handleEvent);

    beforeAll(() => {
      jest.clearAllMocks();

      application?.stop();
      document.body.innerHTML = `
        <div
          id="test"
          class="hide-me"
          data-controller="w-init"
          data-w-init-delay-value="1_000"
          data-w-init-ready-class="ready"
          data-w-init-remove-class="hide-me"
        >
          Test body
        </div>
      `;

      application = Application.start();
    });

    it('should add a "ready" class and remove specified classes after the delay', async () => {
      const testDiv = document.getElementById('test');

      // expect that before loading finishes (delay), that the div's properties are the same
      application.register('w-init', InitController);

      expect(testDiv.classList).toContain('hide-me');
      expect(testDiv.classList).not.toContain('ready');
      expect(handleEvent).not.toHaveBeenCalled();

      await Promise.resolve(jest.advanceTimersByTime(500));

      expect(testDiv.classList).toContain('hide-me');
      expect(testDiv.classList).not.toContain('ready');
      expect(handleEvent).not.toHaveBeenCalled();

      await Promise.resolve(jest.advanceTimersByTime(1000));

      expect(testDiv.classList).toContain('ready');
      expect(testDiv.classList).not.toContain('hide-me');

      await jest.runAllTimersAsync();
      expect(handleEvent).toHaveBeenCalledTimes(1);
    });
  });

  describe('when using custom event names', () => {
    const handleEvent = jest.fn();
    document.addEventListener('w-init:ready', handleEvent);
    document.addEventListener('custom:event', handleEvent);
    document.addEventListener('other-custom:event', handleEvent);

    beforeAll(() => {
      jest.clearAllMocks();

      application?.stop();

      // intentionally adding extra spaces in the event-value below
      const events = 'custom:event  other-custom:event ';

      document.body.innerHTML = `
        <div
          id="test"
          class="hide-me"
          data-controller="w-init"
          data-w-init-event-value="${events}"
        >
          Test body
        </div>
      `;

      application = Application.start();
    });

    it('should dispatch additional events', async () => {
      expect(handleEvent).not.toHaveBeenCalled();

      application.register('w-init', InitController);

      await Promise.resolve(); // no delay, just wait for the next tick

      expect(handleEvent).toHaveBeenCalledTimes(3);

      expect(handleEvent.mock.calls.map(([event]) => event.type)).toEqual([
        'w-init:ready',
        'custom:event',
        'other-custom:event',
      ]);
    });

    it('should support the ability to block additional events and classes removal', async () => {
      jest.clearAllMocks();

      expect(handleEvent).not.toHaveBeenCalled();

      document.addEventListener(
        'w-init:ready',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );

      const article = document.createElement('article');
      article.id = 'article';
      article.innerHTML = `<p data-controller="w-init" data-w-init-event-value="custom:event">CONTENT</p>`;

      document.body.append(article);

      await jest.runAllTimersAsync();

      // only once - the w-init, no other events should fire
      expect(handleEvent).toHaveBeenCalledTimes(1);
      expect(handleEvent).toHaveBeenLastCalledWith(
        expect.objectContaining({ type: 'w-init:ready' }),
      );
    });
  });

  describe('when using detail for the dispatched events', () => {
    const handleEvent = jest.fn();

    document.addEventListener('w-init:ready', handleEvent);
    document.addEventListener('my-custom:event', handleEvent);

    const detail = { someMessage: 'some value' };

    beforeAll(() => {
      jest.clearAllMocks();

      application?.stop();

      document.body.innerHTML = `
        <article
          id="test"
          class="test-detail"
          data-controller="w-init"
          data-w-init-detail-value='${JSON.stringify(detail)}'
          data-w-init-event-value='my-custom:event'
        >
          Test body
        </article>
      `;

      application = Application.start();
    });

    it('should dispatch event with a detail', async () => {
      application.register('w-init', InitController);
      await Promise.resolve(); // no delay, just wait for the next tick

      expect(handleEvent).toHaveBeenCalledTimes(2);

      const [[firstEvent], [secondEvent]] = handleEvent.mock.calls;

      expect(firstEvent.type).toEqual('w-init:ready');
      expect(firstEvent.detail).toEqual(detail);

      expect(secondEvent.type).toEqual('my-custom:event');
      expect(secondEvent.detail).toEqual(detail);
    });
  });
});
