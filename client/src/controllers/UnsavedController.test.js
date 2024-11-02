import { Application } from '@hotwired/stimulus';

import { UnsavedController } from './UnsavedController';

jest.useFakeTimers();

describe('UnsavedController', () => {
  const eventNames = [
    'w-unsaved:add',
    'w-unsaved:clear',
    'w-unsaved:ready',
    'w-unsaved:confirm',
    'w-unsaved:watch-edits',
  ];

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
    // https://github.com/jsdom/jsdom/blob/main/lib/jsdom/living/xhr/FormData.webidl

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
      data-w-unsaved-confirmation-value="true"
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
    it('should allow checking for changes to field values', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0);

      document.getElementById('name').value = 'Joe';
      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
    });

    it('should allow checking for when an input is removed', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup();

      // setup should not fire any event
      expect(events['w-unsaved:add']).toHaveLength(0);

      const input = document.getElementById('name');

      input.remove();

      await jest.runAllTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
    });

    it('should ignore when non-inputs are added', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0); // Ensure no initial events

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0); // Verify no events after setup

      // Act (simulate the addition of a paragraph)
      const paragraph = document.createElement('p');
      paragraph.id = 'paraName';
      paragraph.textContent = 'This is a new paragraph'; // Add some content for clarity
      document.getElementsByTagName('form')[0].appendChild(paragraph); // paragraph is added

      await jest.runAllTimersAsync();

      // Assert (verify no events were fired)
      expect(events['w-unsaved:add']).toHaveLength(0);
    });

    it('should fire an event when a textarea is added', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0); // Ensure no initial events

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0); // Verify no events after setup

      // Act (simulate adding a textarea with value)
      const textarea = document.createElement('textarea');
      textarea.value = 'Some initial content';
      textarea.id = 'taName';
      document.getElementsByTagName('form')[0].appendChild(textarea);

      await jest.runAllTimersAsync(); // Allow any timers to trigger

      // Assert (verify event was fired)
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
    });

    it('should fire an event when a nested input (select) is added', async () => {
      // Arrange
      expect(events['w-unsaved:add']).toHaveLength(0); // Ensure no initial events

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0); // Verify no events after setup

      // Act
      const div = document.createElement('div');
      const select = document.createElement('select');
      select.id = 'mySelect';

      const option1 = document.createElement('option');
      option1.value = 'option1';
      option1.textContent = 'Option 1';
      select.appendChild(option1);

      const option2 = document.createElement('option');
      option2.value = 'option2';
      option2.textContent = 'Option 2';
      select.appendChild(option2);

      div.appendChild(select);
      document.body.getElementsByTagName('form')[0].appendChild(div);

      await jest.runAllTimersAsync();

      // Assert
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
    });
  });

  describe('showing a confirmation message when exiting the browser tab', () => {
    const mockBrowserClose = () =>
      new Promise((resolve) => {
        const event = new Event('beforeunload', { cancelable: true });
        window.dispatchEvent(event);
        // If the event is prevented, the browser will show a confirmation message.
        resolve(event.defaultPrevented);
      });

    it('should not show a confirmation message if no edits exist', async () => {
      await setup();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
      expect(events['w-unsaved:confirm']).toHaveLength(0);
    });

    it('should show a confirmation message if forced', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
          data-w-unsaved-confirmation-value="true"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      // Should immediately set the form as having edits
      const form = document.querySelector('form');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );

      // Should dispatch an add event with the type of edits
      // so that the user can be warned
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');

      // Should not dispatch a watch-edits event
      expect(events['w-unsaved:watch-edits']).toHaveLength(0);

      const result = await mockBrowserClose();

      expect(result).toEqual(true);
      expect(events['w-unsaved:confirm']).toHaveLength(1);

      // Should still consider the form as having edits after an edit is made
      const input = document.getElementById('name');
      input.value = 'James Sunderland';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:clear']).toHaveLength(0);
    });

    it('should not show a confirmation message if forced but confirmation value is false', async () => {
      await setup(`
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
          data-w-unsaved-confirmation-value="false"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</submit>
        </form>
      </section>`);

      // Should immediately set the form as having edits
      const form = document.querySelector('form');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );

      // Should dispatch an add event with the type of edits
      // so that the user can be warned
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');

      // Should not dispatch a watch-edits event
      expect(events['w-unsaved:watch-edits']).toHaveLength(0);

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
      expect(events['w-unsaved:confirm']).toHaveLength(0);

      // Should still consider the form as having edits after an edit is made
      const input = document.getElementById('name');
      input.value = 'James Sunderland';
      input.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:clear']).toHaveLength(0);
    });

    it('should allow a confirmation message to show before the browser closes', async () => {
      await setup();

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(true);
      expect(events['w-unsaved:confirm']).toHaveLength(1);
    });

    it('should not show a confirmation message if there are edits but the form is being submitted', async () => {
      await setup();

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      // mock submitting the form
      document.getElementById('form').dispatchEvent(new Event('submit'));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
      expect(events['w-unsaved:confirm']).toHaveLength(0);
    });

    it('should not show a confirmation message if the confirm event is prevented', async () => {
      const preventConfirm = jest
        .fn()
        .mockImplementation((e) => e.preventDefault());
      document.addEventListener('w-unsaved:confirm', preventConfirm);
      await setup();

      document
        .getElementById('name')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
      expect(events['w-unsaved:confirm']).toHaveLength(1);
      expect(events['w-unsaved:confirm'][0].defaultPrevented).toEqual(true);
      expect(preventConfirm).toHaveBeenCalledTimes(1);
      document.removeEventListener('w-unsaved:confirm', preventConfirm);
    });
  });
});
