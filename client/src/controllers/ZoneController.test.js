import { Application } from '@hotwired/stimulus';
import { ZoneController } from './ZoneController';

jest.useFakeTimers();

describe('ZoneController', () => {
  let application;

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();
    application.register('w-zone', ZoneController);

    await Promise.resolve();
  };

  afterEach(() => {
    application?.stop();
    jest.clearAllMocks();
  });

  describe('activate method', () => {
    it('should add active class to the element', async () => {
      await setup(`
        <div
          class="drop-zone"
          data-controller="w-zone"
          data-w-zone-active-class="hovered"
          data-action="dragover->w-zone#activate"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');
      element.dispatchEvent(new Event('dragover'));
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(true);
    });
  });

  describe('deactivate method', () => {
    it('should remove active class from the element', async () => {
      await setup(`
        <div
          class="drop-zone hovered"
          data-controller="w-zone"
          data-w-zone-mode-value="active"
          data-w-zone-active-class="hovered"
          data-action="dragleave->w-zone#deactivate"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');
      element.dispatchEvent(new Event('dragleave'));
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(false);
    });

    it('should not throw an error if active class is not present', async () => {
      await setup(`
        <div
          class="drop-zone"
          data-controller="w-zone"
          data-w-zone-active-class="hovered"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');
      expect(() => element.dispatchEvent(new Event('dragleave'))).not.toThrow();
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(false);
    });
  });

  describe('noop method', () => {
    it('should allow for arbitrary stimulus actions via the noop method', async () => {
      await setup(`
        <div
          class="drop-zone"
          data-controller="w-zone"
          data-w-zone-active-class="hovered"
          data-action="drop->w-zone#noop:prevent"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');
      const dropEvent = new Event('drop', { bubbles: true, cancelable: true });
      element.dispatchEvent(dropEvent);
      await jest.runAllTimersAsync();
      expect(dropEvent.defaultPrevented).toBe(true);
    });
  });

  describe('delay value', () => {
    it('should delay the mode change by the provided value', async () => {
      await setup(`
        <div
          class="drop-zone"
          data-controller="w-zone"
          data-w-zone-active-class="active"
          data-w-zone-delay-value="100"
          data-action="dragover->w-zone#activate dragleave->w-zone#deactivate"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');

      element.dispatchEvent(new Event('dragover'));
      await Promise.resolve(jest.advanceTimersByTime(50));

      expect(element.classList.contains('active')).toBe(false);

      await jest.advanceTimersByTime(55);
      expect(element.classList.contains('active')).toBe(true);

      // deactivate should take twice as long (100 x 2 = 200ms)

      element.dispatchEvent(new Event('dragleave'));

      await Promise.resolve(jest.advanceTimersByTime(180));

      expect(element.classList.contains('active')).toBe(true);

      await Promise.resolve(jest.advanceTimersByTime(20));
      expect(element.classList.contains('active')).toBe(false);
    });
  });

  describe('example usage for drag & drop', () => {
    it('should handle multiple drag-related events correctly', async () => {
      await setup(`
        <div
          class="drop-zone"
          data-controller="w-zone"
          data-w-zone-active-class="hovered"
          data-action="dragover->w-zone#activate:prevent dragleave->w-zone#deactivate dragend->w-zone#deactivate"
        ></div>
      `);

      const element = document.querySelector('.drop-zone');

      // Simulate dragover
      const dragoverEvent = new Event('dragover', {
        bubbles: true,
        cancelable: true,
      });
      element.dispatchEvent(dragoverEvent);
      expect(dragoverEvent.defaultPrevented).toBe(true);
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(true);

      // Simulate dragleave
      element.dispatchEvent(new Event('dragleave'));
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(false);

      // Simulate dragover again for dragend
      element.dispatchEvent(dragoverEvent);
      expect(dragoverEvent.defaultPrevented).toBe(true);
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(true);

      // Simulate dragend
      element.dispatchEvent(new Event('dragend'));
      await jest.runAllTimersAsync();
      expect(element.classList.contains('hovered')).toBe(false);
    });
  });

  describe('initial mode value based on class', () => {
    it('should set mode value to active when initial class matches active class', async () => {
      await setup(`
        <div
          class="mode-zone"
          data-controller="w-zone"
          data-w-zone-active-class="mode-zone"
        ></div>
      `);
      const element = document.querySelector('div');
      await jest.runAllTimersAsync();
      expect(element.getAttribute('data-w-zone-mode-value')).toBe('active');
    });

    it('should set mode value to empty when initial class matches inactive class', async () => {
      await setup(`
        <div
          class="inactive"
          data-controller="w-zone"
          data-w-zone-inactive-class="inactive"
        ></div>
      `);

      const element = document.querySelector('div');
      await jest.runAllTimersAsync();
      expect(element.getAttribute('data-w-zone-mode-value')).toBe('');
    });
  });

  describe('switch method', () => {
    it('should add active classes & remove inactive classes when key is truthy', async () => {
      await setup(`
        <div
          class="switch-zone w-hidden"
          data-controller="w-zone"
          data-action="custom-event->w-zone#switch"
          data-w-zone-active-class=""
          data-w-zone-inactive-class="w-hidden"
          data-w-zone-switch-key-value="active"
        ></div>
      `);

      const element = document.querySelector('.switch-zone');
      const event = new CustomEvent('custom-event', {
        detail: { active: true },
      });
      element.dispatchEvent(event);
      await jest.runAllTimersAsync();
      expect(element.className).toBe('switch-zone');
    });

    it('should add inactive classes & remove active classes when key is falsy', async () => {
      await setup(`
        <div
          class="switch-zone"
          data-controller="w-zone"
          data-action="custom-event->w-zone#switch"
          data-w-zone-active-class=""
          data-w-zone-inactive-class="w-hidden"
          data-w-zone-switch-key-value="active"
        ></div>
      `);

      const element = document.querySelector('.switch-zone');
      const event = new CustomEvent('custom-event', {
        detail: { active: false },
      });
      element.dispatchEvent(event);
      await jest.runAllTimersAsync();
      expect(element.className).toBe('switch-zone w-hidden');
    });

    it('should add inactive classes & remove active classes when key is negated & event-detail key is truthy', async () => {
      await setup(`
        <div
          class="switch-zone"
          data-controller="w-zone"
          data-w-zone-inactive-class="w-hidden"
          data-action="custom-event->w-zone#switch"
          data-w-zone-switch-key-value="!active"
        ></div>
      `);

      const element = document.querySelector('.switch-zone');
      const event = new CustomEvent('custom-event', {
        detail: { active: true },
      });
      element.dispatchEvent(event);
      await jest.runAllTimersAsync();
      expect(element.className).toBe('switch-zone w-hidden'); // Negated key means truthy value results in inactive
    });

    it('should use the fallback key of active when no key is provided', async () => {
      await setup(`
        <div
          class="switch-zone w-hidden"
          data-controller="w-zone"
          data-w-zone-active-class=""
          data-w-zone-inactive-class="w-hidden"
          data-action="custom-event->w-zone#switch"
        ></div>
      `);

      const element = document.querySelector('.switch-zone');
      const event = new CustomEvent('custom-event', {
        detail: { active: true },
      });
      element.dispatchEvent(event);
      await jest.runAllTimersAsync();
      expect(element.className).toBe('switch-zone');
    });

    it('should prioritize event-detail over params when both are present', async () => {
      await setup(`
        <div
          class="switch-zone w-hidden"
          data-controller="w-zone"
          data-w-zone-active-class=""
          data-w-zone-inactive-class="w-hidden"
          data-action="custom-event->w-zone#switch"
        ></div>
      `);

      const element = document.querySelector('.switch-zone');
      const event = new CustomEvent('custom-event', {
        detail: { active: true },
      });
      event.params = { active: false };

      element.dispatchEvent(event);
      await jest.runAllTimersAsync();
      expect(element.className).toBe('switch-zone'); // event-detail take precedence
    });
  });
});
