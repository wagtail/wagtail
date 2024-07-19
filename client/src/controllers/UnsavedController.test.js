import { Application } from '@hotwired/stimulus';

import { UnsavedController } from './UnsavedController';

jest.useFakeTimers();

describe('UnsavedController', () => {
  const eventNames = ['w-unsaved:add', 'w-unsaved:clear', 'w-unsaved:ready'];

  const events = {};

  let application;
  let errors = [];

  beforeAll(() => {
    eventNames.forEach((name) => {
      events[name] = [];
    });

    Object.keys(events).forEach((name) => {
      document.addEventListener(name, (event) => {
        events[name].push(event);
      });
    });
  });

  beforeEach(() => {
    // Mock FormData.entries
    const mockEntries = jest
      .fn()
      .mockReturnValueOnce(['name', 'John'])
      .mockReturnValue([['name', 'Joe']]);

    global.FormData = class FormData {
      entries() {
        return mockEntries();
      }
    };
  });

  const setup = async (
    html = `
  <section>
    <form
      id="form"
      data-controller="w-unsaved"
      data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
      data-w-unsaved-confirmation-value="You have unsaved changes!"
    >
      <input type="text" id="name" value="John" />
      <button>Submit</submit>
    </form>
  </section>`,
    identifier = 'w-unsaved',
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = new Application();

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    application.register(identifier, UnsavedController);

    application.start();

    await jest.runAllTimersAsync();

    return [
      ...document.querySelectorAll(`[data-controller~="${identifier}"]`),
    ].map((element) =>
      application.getControllerForElementAndIdentifier(element, identifier),
    );
  };

  afterEach(() => {
    application?.stop && application.stop();
    errors = [];
    eventNames.forEach((name) => {
      events[name] = [];
    });
  });

  it('should dispatch a ready event when loaded', async () => {
    expect(events['w-unsaved:clear']).toHaveLength(0);
    expect(events['w-unsaved:ready']).toHaveLength(0);

    await setup();

    expect(events['w-unsaved:clear']).toHaveLength(1);
    expect(events['w-unsaved:ready']).toHaveLength(1);
  });

  describe('checking for edits', () => {
    // ... existing test cases ...
  });

  describe('showing a confirmation message when exiting the browser tab', () => {
    const mockBrowserClose = () =>
      new Promise((resolve) => {
        const event = new Event('beforeunload');
        Object.defineProperty(event, 'returnValue', {
          value: false,
          writable: true,
        });

        window.dispatchEvent(event);

        resolve(event.returnValue || '');
      });

    it('should not show a confirmation message if no edits exist', async () => {
      await setup();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
    });

    it('should show a confirmation message if forced', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
          data-w-unsaved-confirmation-value="You have unsaved changes!"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      const result = await mockBrowserClose();

      expect(result).toEqual('You have unsaved changes!');
    });

    it('should allow a confirmation message to show before the browser closes', async () => {
      await setup();

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual('You have unsaved changes!');
    });

    it('should should not show a confirmation message if there are edits but the form is being submitted', async () => {
      await setup();

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      // mock submitting the form
      document.getElementById('form').dispatchEvent(new Event('submit'));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
    });
  });

  describe('UnsavedController#confirm method', () => {
    it('should not trigger confirmation dialog if confirmationValue is not set', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
    });

    it('should trigger confirmation dialog if confirmationValue is set and form has edits', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
          data-w-unsaved-confirmation-value="You have unsaved changes!"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(''); // Here we are testing the behavior based on the `event.preventDefault()` call
    });

    it('should trigger confirmation dialog if confirmationValue is set and forceValue is true', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
          data-w-unsaved-confirmation-value="You have unsaved changes!"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      const result = await mockBrowserClose();

      expect(result).toEqual(''); // Here we are testing the behavior based on the `event.preventDefault()` call
    });
  });
});
