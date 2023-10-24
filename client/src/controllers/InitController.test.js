import { Application } from '@hotwired/stimulus';
import { InitController } from './InitController';

jest.useFakeTimers();

describe('InitController', () => {
  let application;

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('default behaviour', () => {
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
});
