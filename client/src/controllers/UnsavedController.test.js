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

  const setup = async (
    html = /* html */ `
  <section>
    <form
      id="form"
      data-controller="w-unsaved"
      data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
      data-w-unsaved-confirmation-value="true"
    >
      <input type="text" id="name" name="name" value="John" />
      <input type="hidden" name="csrfmiddlewaretoken" value="potatoken" />
      <input type="hidden" name="next" value="/next/url/" />
      <button>Submit</button>
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

    // Wait for the initial delay of setting up the initial form data
    await jest.runOnlyPendingTimersAsync();
    // Trigger the first check interval
    await jest.runOnlyPendingTimersAsync();

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

      // The change has not been detected
      const form = document.querySelector('form');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );

      // Wait for 500ms to trigger the check
      await jest.advanceTimersByTimeAsync(500);

      // Now the change should be detected
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );

      // But the event should not have fired yet due to the debounce
      expect(events['w-unsaved:add']).toHaveLength(0);

      // Wait for more than 500ms to trigger another check, but less than the
      // debounced notify time of 30ms
      await jest.advanceTimersByTimeAsync(510);

      // The event should still not have fired
      expect(events['w-unsaved:add']).toHaveLength(0);

      // Now advance time to trigger the debounced notify
      await jest.advanceTimersByTimeAsync(20);

      // Now the event should have fired
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
    });

    it('should allow checking for when an input is removed', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup();

      // setup should not fire any event
      expect(events['w-unsaved:add']).toHaveLength(0);

      const input = document.getElementById('name');

      input.remove();

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

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

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      // Assert (verify no events were fired)
      expect(events['w-unsaved:add']).toHaveLength(0);
    });

    it('should ignore excluded field names', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0); // Ensure no initial events

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0); // Verify no events after setup

      const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
      csrf.value = 'tomatoken';
      const next = document.querySelector('input[name="next"]');
      next.value = '/another/url/';

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

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
      textarea.name = 'taName';
      document.getElementsByTagName('form')[0].appendChild(textarea);

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

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
      select.name = 'mySelect';

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

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      // Assert
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
    });

    it('should detect changes to file inputs', async () => {
      const files = {
        multiple: [
          new File(['file contents'], 'test.txt', {
            type: 'text/plain',
          }),
        ],
        single: [],
      };

      // JSDOM does not yet support setting File inputs programmatically,
      // see https://github.com/jsdom/jsdom/issues/1272.
      // Mock FormData instead of the input element, as JSDOM's FormData uses
      // the underlying HTMLInputElement-Impl and ignores modifications to
      // HTMLInputElement.files.
      class MockFormData extends FormData {
        get(key) {
          return key in files ? files[key][0] : super.get(key);
        }

        getAll(key) {
          return key in files ? files[key] : super.getAll(key);
        }
      }
      const formDataSpy = jest
        .spyOn(window, 'FormData')
        .mockImplementation((form) => new MockFormData(form));

      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup(/* html */ `
        <section>
          <form
            id="form"
            data-controller="w-unsaved"
            data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
            data-w-unsaved-confirmation-value="true"
          >
            <input type="file" multiple id="multiple" name="multiple" />
            <input type="file" id="single" name="single" />
            <button>Submit</button>
          </form>
        </section>
      `);

      expect(events['w-unsaved:add']).toHaveLength(0);

      files.multiple.push(
        new File(['another file'], 'example.png', {
          type: 'image/png',
        }),
      );

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');

      files.single.push(
        new File(['single file'], 'document.pdf', {
          type: 'application/pdf',
        }),
      );

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(2);
      expect(events['w-unsaved:add'][1]).toHaveProperty('detail.type', 'edits');

      // Should also detect removing files
      files.multiple = [];
      files.single = [];

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(3);
      expect(events['w-unsaved:add'][2]).toHaveProperty('detail.type', 'edits');

      formDataSpy.mockRestore();
    });
  });

  describe('changing the check interval value', () => {
    it('should update the check interval when the value changes', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup();

      expect(events['w-unsaved:add']).toHaveLength(0);

      document.getElementById('name').value = 'Joe';

      // The change has not been detected
      const form = document.querySelector('form');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );

      // Wait for 400ms to simulate some time passing but before the default
      // 500ms check interval
      await jest.advanceTimersByTimeAsync(400);

      // The change should still not be detected
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );

      form.setAttribute('data-w-unsaved-check-interval-value', '1_945');

      // The change should still not be detected
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );

      // Wait for 1600ms to far exceed the original 500ms check interval and
      // additional 30ms notify delay, but still before the new 1,945ms interval
      await jest.advanceTimersByTimeAsync(1_600);

      // The change should still not be detected
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );
      // And no event should have fired yet
      expect(events['w-unsaved:add']).toHaveLength(0);

      // Wait the remaining time to trigger the new check interval
      await jest.advanceTimersByTimeAsync(345);

      // The change should now be detected
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );

      // But the event should not have fired yet due to the debounce
      expect(events['w-unsaved:add']).toHaveLength(0);

      // Wait for the next check interval in case of consecutive changes
      await jest.advanceTimersByTimeAsync(1_945);

      // The form is still marked as dirty
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );

      // But the event should not have fired yet due to the debounce
      expect(events['w-unsaved:add']).toHaveLength(0);

      // Wait for additional 30ms to trigger the debounced notify
      await jest.advanceTimersByTimeAsync(30);

      // Now the event should have fired
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
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
      await setup(/* html */ `
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
          data-w-unsaved-confirmation-value="true"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" name="name" value="John" />
          <button>Submit</button>
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

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:clear']).toHaveLength(0);
    });

    it('should not show a confirmation message if forced but confirmation value is false', async () => {
      await setup(/* html */ `
      <section>
        <form
          data-controller="w-unsaved"
          data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
          data-w-unsaved-confirmation-value="false"
          data-w-unsaved-force-value="true"
        >
          <input type="text" id="name" value="John" />
          <button>Submit</button>
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

      await jest.runOnlyPendingTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:clear']).toHaveLength(0);
    });

    it('should allow a confirmation message to show before the browser closes', async () => {
      await setup();

      document.getElementById('name').value = 'Changed person';

      await jest.runOnlyPendingTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(true);
      expect(events['w-unsaved:confirm']).toHaveLength(1);
    });

    it('should not show a confirmation message if there are edits but the form is being submitted', async () => {
      await setup();

      document.getElementById('name').value = 'Changed cat';

      await jest.runOnlyPendingTimersAsync();

      // mock submitting the form
      document.getElementById('form').dispatchEvent(new Event('submit'));

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

      document.getElementById('name').value = 'Changed doggo';

      await jest.runOnlyPendingTimersAsync();

      const result = await mockBrowserClose();

      expect(result).toEqual(false);
      expect(events['w-unsaved:confirm']).toHaveLength(1);
      expect(events['w-unsaved:confirm'][0].defaultPrevented).toEqual(true);
      expect(preventConfirm).toHaveBeenCalledTimes(1);
      document.removeEventListener('w-unsaved:confirm', preventConfirm);
    });
  });

  describe('clearing tracked changes and messages', () => {
    it('should allow clearing via events', async () => {
      await setup();

      expect(events['w-unsaved:ready']).toHaveLength(1);
      expect(events['w-unsaved:add']).toHaveLength(0);
      expect(events['w-unsaved:clear']).toHaveLength(1);

      const form = document.querySelector('form');
      const button = document.createElement('button');
      const input = document.getElementById('name');
      button.type = 'button';
      button.setAttribute('data-action', 'w-unsaved#clear');
      form.appendChild(button);

      input.value = 'Changed person';

      await jest.runOnlyPendingTimersAsync();
      await jest.runOnlyPendingTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:clear']).toHaveLength(1);

      // Click the clear button
      button.click();
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );
      await jest.runOnlyPendingTimersAsync();
      await jest.runOnlyPendingTimersAsync();

      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:clear']).toHaveLength(2);

      input.value = 'Changed person again';

      await jest.runOnlyPendingTimersAsync();
      await jest.runOnlyPendingTimersAsync();

      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'true',
      );
      expect(events['w-unsaved:add']).toHaveLength(2);
      expect(events['w-unsaved:clear']).toHaveLength(2);
    });
  });

  describe('handling comments data', () => {
    const mockDirtyComments = () => {
      window.comments = {
        commentApp: {
          selectors: {
            selectIsDirty: jest.fn().mockReturnValue(true),
          },
          store: {
            getState: jest.fn(),
          },
        },
      };
    };

    afterEach(() => {
      delete window.comments;
    });

    it('should track comments app data instead of the form inputs', async () => {
      expect(events['w-unsaved:add']).toHaveLength(0);

      await setup(/* html */ `
        <section>
          <form
            id="form"
            data-controller="w-unsaved"
            data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
            data-w-unsaved-confirmation-value="true"
          >
            <input type="text" id="title" name="title" value="Some Page" />
            <div id="comments-output" hidden="">
              <input
                type="hidden"
                name="comments-TOTAL_FORMS"
                id="id_comments-TOTAL_FORMS"
                value="0"
              />
              <input
                type="hidden"
                name="comments-INITIAL_FORMS"
                id="id_comments-INITIAL_FORMS"
                value="0"
              />
              <input
                type="hidden"
                name="comments-MIN_NUM_FORMS"
                id="id_comments-MIN_NUM_FORMS"
                value="0"
              />
              <input
                type="hidden"
                name="comments-MAX_NUM_FORMS"
                id="id_comments-MAX_NUM_FORMS"
                value=""
              />
            </div>
            <button>Submit</button>
          </form>
        </section>
      `);

      expect(events['w-unsaved:add']).toHaveLength(0);

      // Simulate updating the comments form data
      const output = document.getElementById('comments-output');
      output.innerHTML = /* html */ `
        <input
          type="hidden"
          name="comments-TOTAL_FORMS"
          id="id_comments-TOTAL_FORMS"
          value="1"
        />
        <input
          type="hidden"
          name="comments-INITIAL_FORMS"
          id="id_comments-INITIAL_FORMS"
          value="0"
        />
        <input
          type="hidden"
          name="comments-MIN_NUM_FORMS"
          id="id_comments-MIN_NUM_FORMS"
          value="0"
        />
        <input
          type="hidden"
          name="comments-MAX_NUM_FORMS"
          id="id_comments-MAX_NUM_FORMS"
          value=""
        />
        <fieldset>
          <input
            type="hidden"
            name="comments-0-DELETE"
            id="id_comments-0-DELETE"
            value=""
          />
          <input
            type="hidden"
            name="comments-0-resolved"
            id="id_comments-0-resolved"
            value=""
          />
          <input
            type="hidden"
            name="comments-0-id"
            id="id_comments-0-id"
            value=""
          />
          <input
            type="hidden"
            name="comments-0-contentpath"
            id="id_comments-0-contentpath"
            value="title"
          />
          <input
            type="hidden"
            name="comments-0-text"
            id="id_comments-0-text"
            value="Nice"
          />
          <input
            type="hidden"
            name="comments-0-position"
            id="id_comments-0-position"
            value=""
          />
        </fieldset>
      `;

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      // Should not be detected yet
      expect(events['w-unsaved:add']).toHaveLength(0);
      const form = document.querySelector('form');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );
      expect(form.getAttribute('data-w-unsaved-has-comments-value')).toEqual(
        'false',
      );

      // Simulate comments app reporting dirty state
      mockDirtyComments();

      // Run interval to check for changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      // Now changes should be detected from the comments app
      expect(events['w-unsaved:add']).toHaveLength(1);
      expect(events['w-unsaved:add'][0]).toHaveProperty('detail.type', 'edits');
      expect(form.getAttribute('data-w-unsaved-has-edits-value')).toEqual(
        'false',
      );
      expect(form.getAttribute('data-w-unsaved-has-comments-value')).toEqual(
        'true',
      );
    });
  });
});
