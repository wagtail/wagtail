/* eslint-disable @typescript-eslint/no-use-before-define */

import { Application } from '@hotwired/stimulus';

import { FormsetController } from './FormsetController';

jest.useFakeTimers();

describe('FormsetController', () => {
  const eventNames = [
    'change',
    'custom:event',
    'w-formset:ready',
    'w-formset:adding',
    'w-formset:added',
    'w-formset:removing',
    'w-formset:removed',
  ];

  const events = {};

  let application;
  let errors = [];

  const setup = async (
    html = `
  <form data-controller="w-formset">
    <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
    <input type="hidden" name="form-INITIAL_FORMS" value="2">
    <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
    <input type="hidden" name="form-MAX_NUM_FORMS" value="5" data-w-formset-target="maxFormsInput">
    <ul data-w-formset-target="forms">
      <li data-w-formset-target="child">
        <input type="text" name="form-0-name">
        <input type="hidden" name="form-0-DELETE" data-w-formset-target="deleteInput">
        <button type="button" value="Delete" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="child">
        <input type="text" name="form-1-name">
        <input type="hidden" name="form-1-DELETE" data-w-formset-target="deleteInput">
        <button type="button" value="Delete" data-action="w-formset#delete">Delete</button>
      </li>
    </ul>
    <button id="add" type="button" data-action="w-formset#add">Add</button>
    <template data-w-formset-target="template">
      <li data-w-formset-target="child">
        <input type="text" name="form-__prefix__-name">
        <input type="hidden" name="form-__prefix__-DELETE" data-w-formset-target="deleteInput">
        <button type="button" value="Delete" data-action="w-formset#delete">Delete</button>
        <script>document.dispatchEvent(new CustomEvent('custom:event', { detail: { field: document.querySelector('[name="form-__prefix__-name"]') } }), { bubbles: true, cancelable: false });</script>
      </li>
    </template>
  </form>`,
    { identifier = 'w-formset' } = {},
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    application.register(identifier, FormsetController);

    application.start();

    await jest.runAllTimersAsync();

    return [
      ...document.querySelectorAll(`[data-controller~="${identifier}"]`),
    ].map((element) =>
      application.getControllerForElementAndIdentifier(element, identifier),
    );
  };

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

  afterEach(() => {
    document.body.innerHTML = '';
    application?.stop && application.stop();
    errors = [];
    eventNames.forEach((name) => {
      events[name] = [];
    });
  });

  describe('general', () => {
    it('should dispatch a ready event when ready & not trigger change events for initial elements', async () => {
      expect(events.change).toHaveLength(0);
      expect(events['w-formset:added']).toHaveLength(0);
      expect(events['w-formset:ready']).toHaveLength(0);

      await setup();

      expect(events['w-formset:added']).toHaveLength(0);
      expect(events.change).toHaveLength(0);

      expect(events['w-formset:ready']).toHaveLength(1);

      // check it syncs the total forms number
      expect(document.querySelector('[name="form-TOTAL_FORMS"').value).toEqual(
        '2',
      );
    });

    describe('error handling', () => {
      it('should handle errors when the management field for total forms count is not set up correctly', async () => {
        expect(errors).toEqual([]);

        await setup(`
      <form data-controller="w-formset">
      </form>
      `);

        expect(errors).toHaveLength(1);
        expect(errors).toHaveProperty(
          '0.error.message',
          'Missing target element "totalFormsInput" for "w-formset" controller',
        );
      });

      it('should handle errors when the management field for min forms count is not set up correctly', async () => {
        expect(errors).toEqual([]);

        await setup(`
      <form data-controller="w-formset">
        <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
      </form>
      `);

        expect(errors).toHaveLength(1);
        expect(errors).toHaveProperty(
          '0.error.message',
          'Missing target element "minFormsInput" for "w-formset" controller',
        );
      });

      it('should handle errors when the management field for max forms count is not set up correctly', async () => {
        await setup(`
        <form data-controller="w-formset">
          <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
          <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
        </form>
        `);

        expect(errors).toHaveLength(1);

        // last error on initialization has an inner error
        expect(errors).toHaveProperty(
          '0.error.message',
          'Missing target element "maxFormsInput" for "w-formset" controller',
        );
      });

      it('should report if the template structure is malformed', async () => {
        await setup(`
        <form data-controller="w-formset">
          <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
          <input type="hidden" name="form-INITIAL_FORMS" value="2">
          <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
          <input type="hidden" name="form-MAX_NUM_FORMS" value="10" data-w-formset-target="maxFormsInput">
          <ul data-w-formset-target="forms"></ul>
          <button id="add" type="button" data-action="w-formset#add">Add</button>
          <template data-w-formset-target="template">
            _NOT_CORRECT_
          </template>
        </form>`);

        expect(errors).toHaveLength(0);

        document.getElementById('add').click();

        await jest.runAllTimersAsync();

        expect(errors).toHaveLength(1);

        expect(errors).toHaveProperty(
          '0.error.message',
          'Invalid template content, must be a single node.',
        );
      });

      it('should report when deleting a form the delete button is not inside a child form', async () => {
        await setup(`
        <form data-controller="w-formset">
          <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
          <input type="hidden" name="form-INITIAL_FORMS" value="2">
          <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
          <input type="hidden" name="form-MAX_NUM_FORMS" value="10" data-w-formset-target="maxFormsInput">
          <ul data-w-formset-target="forms">
            <li id="item-0" data-w-formset-target="child" data-w-formset-target="deleteInput">
              <input type="text" name="form-0-name">
              <input type="hidden" name="form-0-DELETE">
            </li>
            <button id="item-0-delete" type="button" value="Delete" data-action="w-formset#delete">Delete</button>
          </ul>
        </form>`);

        expect(errors).toHaveLength(0);

        document.getElementById('item-0-delete').click();

        await jest.runAllTimersAsync();

        expect(errors).toHaveLength(1);

        expect(errors).toHaveProperty(
          '0.error.message',
          'Could not find child form target for event target: [object HTMLButtonElement].',
        );
      });
    });
  });

  describe('adding children', () => {
    it('should support the ability to add a child form', async () => {
      expect(events.change).toHaveLength(0);
      expect(events['custom:event']).toHaveLength(0);
      expect(events['w-formset:added']).toHaveLength(0);
      expect(events['w-formset:adding']).toHaveLength(0);

      await setup();

      expect(document.querySelectorAll('li')).toHaveLength(2);

      document.getElementById('add').click();

      expect(events['w-formset:adding']).toHaveLength(1);
      expect(events['w-formset:adding']).toHaveProperty('0.detail', {
        formIndex: 2,
      });

      await jest.runAllTimersAsync();

      // It should have added another element from the template, replacing `__prefix__`
      expect(document.querySelectorAll('li')).toHaveLength(3);
      expect(
        document
          .querySelectorAll('li')[2]
          .innerHTML.split('\n')
          .map((str) => str.trim())
          .filter(Boolean),
      ).toEqual([
        '<input type="text" name="form-2-name">',
        '<input type="hidden" name="form-2-DELETE" data-w-formset-target="deleteInput">',
        '<button type="button" value="Delete" data-action="w-formset#delete">Delete</button>',
        expect.stringContaining(
          // script snippet
          `{ field: document.querySelector('[name="form-2-name"]') }`,
        ),
      ]);

      // should dispatch events
      expect(events['w-formset:added']).toHaveLength(1);
      expect(events['w-formset:added']).toHaveProperty('0.detail', {
        formIndex: 2,
      });

      expect(events.change).toHaveLength(1);
      expect(events.change).toHaveProperty(
        '0.target',
        document.querySelector('[name="form-TOTAL_FORMS"'),
      );

      expect(document.querySelector('[name="form-TOTAL_FORMS"').value).toEqual(
        '3',
      );

      // should run any scripts in the provided child template
      expect(events['custom:event']).toHaveLength(1);
      expect(events['custom:event']).toHaveProperty('0.detail', {
        field: document.querySelector('[name="form-2-name"]'),
      });
    });

    it('should support the prevention of child addition with event listeners', async () => {
      document.addEventListener(
        'w-formset:adding',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );

      await setup();

      expect(document.querySelectorAll('li')).toHaveLength(2);

      document.getElementById('add').click();

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li')).toHaveLength(2);

      document.getElementById('add').click();

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li')).toHaveLength(3);
    });

    it('should limit the addition once the MAX_NUM has been reached', async () => {
      // max is 5

      await setup();

      await jest.runAllTimersAsync(document.getElementById('add').click());
      await jest.runAllTimersAsync(document.getElementById('add').click());
      await jest.runAllTimersAsync(document.getElementById('add').click());

      expect(document.querySelectorAll('li:not([hidden])')).toHaveLength(5);

      // delete one
      await jest.runAllTimersAsync(
        document.querySelector('[value="Delete"]').click(),
      );

      expect(document.querySelectorAll('li:not([hidden])')).toHaveLength(4);

      await jest.runAllTimersAsync(document.getElementById('add').click());

      expect(document.querySelectorAll('li:not([hidden])')).toHaveLength(5);

      await jest.runAllTimersAsync(document.getElementById('add').click());

      expect(document.querySelectorAll('li:not([hidden])')).toHaveLength(5);
    });
  });

  describe('deleting children', () => {
    it('should support the deletion of a child with a delete button', async () => {
      expect(events.change).toHaveLength(0);
      expect(events['w-formset:removing']).toHaveLength(0);
      expect(events['w-formset:removed']).toHaveLength(0);

      await setup();

      expect(document.querySelectorAll('li')).toHaveLength(2);
      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(2);
      expect(
        document.querySelectorAll('li[data-w-formset-target="deleted"]'),
      ).toHaveLength(0);

      document.querySelector('[value="Delete"]').click();

      expect(events['w-formset:removing']).toHaveLength(1);

      await jest.runAllTimersAsync();

      // should change the w-formset target to a deleted one
      expect(document.querySelectorAll('li')).toHaveLength(2);
      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(1);
      expect(
        document.querySelectorAll('li[data-w-formset-target="deleted"]'),
      ).toHaveLength(1);

      // should hide the deleted element
      const deletedChildElement = document.querySelector(
        'li[data-w-formset-target="deleted"]',
      );
      expect(deletedChildElement.hidden).toEqual(true);

      // Dispatches change event on the DELETE input
      expect(events.change).toHaveLength(1);
      expect(events.change).toHaveProperty(
        '0.target',
        document.querySelector('[name="form-0-DELETE"]'),
      );

      // Dispatches a custom event on the removed target
      expect(events['w-formset:removed']).toHaveLength(1);
      expect(events['w-formset:removed']).toHaveProperty(
        '0.target',
        document.querySelector('li'),
      );
    });

    it('should support the prevention of child deletion with event listeners', async () => {
      document.addEventListener(
        'w-formset:removing',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );

      await setup();

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(2);
      expect(
        document.querySelectorAll('li[data-w-formset-target="deleted"]'),
      ).toHaveLength(0);

      document.querySelector('[value="Delete"]').click();
      await jest.runAllTimersAsync();

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(2);
      expect(
        document.querySelectorAll('li[data-w-formset-target="deleted"]'),
      ).toHaveLength(0);

      document.querySelector('[value="Delete"]').click();
      await jest.runAllTimersAsync();

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(1);
      expect(
        document.querySelectorAll('li[data-w-formset-target="deleted"]'),
      ).toHaveLength(1);
    });

    it('should support awaiting animations or transitions before hiding deleted children', async () => {
      await setup();

      // set up class to be added to deleted elements
      document
        .querySelector('form')
        .setAttribute(
          'data-w-formset-deleted-class',
          'animation animation--delete',
        );

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(2);

      document.querySelector('[name="form-0-DELETE"] ~ button').click();

      await Promise.resolve();

      // Check classes have been added but style is not yet hidden

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(1);

      let deletedChildElement = document.querySelector(
        'li[data-w-formset-target="deleted"]',
      );

      expect(deletedChildElement.hidden).toEqual(false);
      expect([...deletedChildElement.classList]).toEqual([
        'animation',
        'animation--delete',
      ]);

      // after the animation runs it should set hidden
      await Promise.resolve(
        deletedChildElement.dispatchEvent(
          new Event('animationend', { bubbles: true }),
        ),
      );

      expect(deletedChildElement.hidden).toEqual(true);

      // check the same but with `transitionend` event

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(1);

      document.querySelector('[name="form-1-DELETE"] ~ button').click();

      await Promise.resolve();

      deletedChildElement = document.querySelector('li:last-child');

      expect(deletedChildElement.hidden).toEqual(false);
      expect([...deletedChildElement.classList]).toEqual([
        'animation',
        'animation--delete',
      ]);

      // after the transition runs it should set hidden
      await Promise.resolve(
        deletedChildElement.dispatchEvent(
          new Event('transitionend', { bubbles: true }),
        ),
      );

      expect(deletedChildElement.hidden).toEqual(true);
    });

    it('should not allow transitions longer than ~300ms', async () => {
      await setup();

      // set up class to be added to deleted elements
      document
        .querySelector('form')
        .setAttribute(
          'data-w-formset-deleted-class',
          'animation animation--delete',
        );

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(2);

      document.querySelector('[name="form-0-DELETE"] ~ button').click();

      await Promise.resolve();

      // Check classes have been added but style is not yet hidden

      expect(
        document.querySelectorAll('li[data-w-formset-target="child"]'),
      ).toHaveLength(1);

      const deletedChildElement = document.querySelector(
        'li[data-w-formset-target="deleted"]',
      );

      expect(deletedChildElement.hidden).toEqual(false);
      expect([...deletedChildElement.classList]).toEqual([
        'animation',
        'animation--delete',
      ]);

      await jest.advanceTimersByTimeAsync(200);

      expect(deletedChildElement.hidden).toEqual(false);

      await jest.advanceTimersByTimeAsync(90);

      expect(deletedChildElement.hidden).toEqual(false);

      await jest.advanceTimersByTimeAsync(60); // total 350ms

      expect(deletedChildElement.hidden).toEqual(true);
    });

    it('should not dispatch change or deleted events if hidden/deleted items are in the initial HTML', async () => {
      // Ensures that POST response with partial formset deletions are not counted as 'newly' deleted items

      expect(events.change).toHaveLength(0);
      expect(events['w-formset:removed']).toHaveLength(0);

      await setup(`
  <form data-controller="w-formset">
    <input type="hidden" name="form-TOTAL_FORMS" value="4" data-w-formset-target="totalFormsInput">
    <input type="hidden" name="form-INITIAL_FORMS" value="4">
    <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
    <input type="hidden" name="form-MAX_NUM_FORMS" value="50" data-w-formset-target="maxFormsInput">
    <ul data-w-formset-target="forms">
      <li data-w-formset-target="child">
        <input type="text" name="form-0-name">
        <input type="hidden" name="form-0-DELETE" data-w-formset-target="deleteInput">
        <button id="form-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="deleted" hidden>
        <input type="text" name="form-1-name">
        <input type="hidden" name="form-1-DELETE" value="1" data-w-formset-target="deleteInput">
        <button id="form-1-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="child">
        <input type="text" name="form-2-name">
        <input type="hidden" name="form-2-DELETE" data-w-formset-target="deleteInput">
        <button id="form-2-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="deleted" hidden>
        <input type="text" name="form-3-name">
        <input type="hidden" name="form-3-DELETE"  value="1" data-w-formset-target="deleteInput">
        <button id="form-3-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
    </ul>
  </form>`);

      expect(events.change).toHaveLength(0);
      expect(events['w-formset:removed']).toHaveLength(0);
    });

    it('should limit the deletion once the MIN_NUM has been reached', async () => {
      await setup(`
  <form data-controller="w-formset">
    <input type="hidden" name="form-TOTAL_FORMS" value="4" data-w-formset-target="totalFormsInput">
    <input type="hidden" name="form-INITIAL_FORMS" value="4">
    <input type="hidden" name="form-MIN_NUM_FORMS" value="2" data-w-formset-target="minFormsInput">
    <input type="hidden" name="form-MAX_NUM_FORMS" value="4" data-w-formset-target="maxFormsInput">
    <ul data-w-formset-target="forms">
      <li data-w-formset-target="child">
        <input type="text" name="form-0-name">
        <input type="hidden" name="form-0-DELETE" data-w-formset-target="deleteInput">
        <button id="form-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="child">
        <input type="text" name="form-1-name">
        <input type="hidden" name="form-1-DELETE" data-w-formset-target="deleteInput">
        <button id="form-1-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="child">
        <input type="text" name="form-2-name">
        <input type="hidden" name="form-2-DELETE" data-w-formset-target="deleteInput">
        <button id="form-2-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
      <li data-w-formset-target="deleted" hidden>
        <input type="text" name="form-3-name">
        <input type="hidden" name="form-3-DELETE" value="1" data-w-formset-target="deleteInput">
        <button id="form-3-delete-button" type="button" data-action="w-formset#delete">Delete</button>
      </li>
    </ul>
  </form>`);

      expect(document.querySelectorAll('li')).toHaveLength(4);
      expect(document.querySelectorAll('li[hidden]')).toHaveLength(1);

      document.getElementById('form-1-delete-button').click();

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li')).toHaveLength(4);
      expect(document.querySelectorAll('li[hidden]')).toHaveLength(2);

      // Deleting the other item should do nothing as minimum is 2
      document.getElementById('form-0-delete-button').click();

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li')).toHaveLength(4);
      expect(document.querySelectorAll('li[hidden]')).toHaveLength(2);
    });
  });

  describe('nested formset controller usage', () => {
    it('should addition of nested child forms', async () => {
      expect(events['w-formset:ready']).toHaveLength(0);

      await setup(getNestedHtml());

      expect(events['w-formset:ready']).toHaveLength(3);

      expect(events['w-formset:ready'].map((event) => event.target)).toEqual([
        document.querySelector('form'),
        document.getElementById('group-0-checklist'),
        document.getElementById('group-1-checklist'),
      ]);

      // check initial total forms are in sync
      expect(document.querySelector('[name="form-TOTAL_FORMS"').value).toBe(
        '2',
      );
      expect(document.querySelector('[name="group-0-TOTAL_FORMS"').value).toBe(
        '4',
      );
      expect(document.querySelector('[name="group-1-TOTAL_FORMS"').value).toBe(
        '3',
      );

      document.getElementById('add-checklist-item-group-0').click();

      expect(events['w-formset:adding']).toHaveLength(1);

      await jest.runAllTimersAsync();

      expect(events['w-formset:added']).toHaveLength(1);
      expect(events['w-formset:added']).toHaveProperty(
        '0.target',
        document.getElementById('group-0-item-4-item'),
      );

      // check the correct TOTAL_FORMS has been updated correctly

      expect(events.change).toHaveLength(1);

      expect(document.querySelector('[name="form-TOTAL_FORMS"').value).toBe(
        '2',
      );
      expect(document.querySelector('[name="group-0-TOTAL_FORMS"').value).toBe(
        '5',
      );
      expect(document.querySelector('[name="group-1-TOTAL_FORMS"').value).toBe(
        '3',
      );
    });

    it('should support the deletion of a nested child with a delete button', async () => {
      await setup(getNestedHtml());

      expect(events['w-formset:ready']).toHaveLength(3);

      expect(document.querySelectorAll('li')).toHaveLength(7);
      expect(document.querySelectorAll('li[hidden]')).toHaveLength(0);

      document.getElementById('group-1-item-1-delete-button').click();

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li[hidden]')).toHaveLength(1);
    });

    it('should support the deletion of outer items without impacting nested element DELETE fields', async () => {
      await setup(getNestedHtml());

      // check all delete values are not set
      expect(
        [...document.querySelectorAll('input[name$="-DELETE"]')]
          .map((input) => input.value)
          .join(''),
      ).toEqual('');

      const firstGroupDeleteInput = document.querySelector(
        '[name="group-0-DELETE"]',
      );

      expect(firstGroupDeleteInput.value).toEqual('');

      // delete the first outer group
      document.getElementById('group-0-delete-button').click();

      await jest.runAllTimersAsync();

      expect(document.getElementById('group-item-0').hidden).toEqual(true);

      expect(events.change).toHaveLength(1);
      expect(firstGroupDeleteInput.value).toEqual('1');
      expect(events.change).toHaveProperty('0.target', firstGroupDeleteInput);

      // check the the other nested DELETE fields are not affected
      expect(
        [
          ...document.querySelectorAll(
            '#group-0-checklist input[name$="-DELETE"]',
          ),
        ]
          .map((input) => input.value)
          .join(''),
      ).toEqual('');

      // delete the second outer group

      const secondGroupDeleteInput = document.querySelector(
        '[name="group-1-DELETE"]',
      );

      expect(secondGroupDeleteInput.value).toEqual('');

      document.getElementById('group-1-delete-button').click();

      await jest.runAllTimersAsync();

      expect(document.getElementById('group-item-1').hidden).toEqual(true);

      expect(events.change).toHaveLength(2);
      expect(events.change).toHaveProperty('1.target', secondGroupDeleteInput);
      expect(secondGroupDeleteInput.value).toEqual('1');
    });

    it('should support addition of outer items with nested elements', async () => {});

    function getNestedHtml() {
      return `
    <form id="outer-form" data-controller="w-formset">
      <fieldset data-w-formset-target="managementFields">
        <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
        <input type="hidden" name="form-INITIAL_FORMS" value="2">
        <input type="hidden" name="form-MIN_NUM_FORMS" value="1">
        <input type="hidden" name="form-MAX_NUM_FORMS" value="5">
      </fieldset>
      <section data-w-formset-target="forms">
        <div id="group-item-0" data-w-formset-target="child">
          <input type="email" name="group-0-email">
          <input type="text" name="group-0-name">
          <button id="group-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
          <fieldset id="group-0-checklist" data-controller="w-formset">
            <legend>Inner checklist</legend>
            <input type="hidden" name="group-0-TOTAL_FORMS" value="4" data-w-formset-target="totalFormsInput"
            <input type="hidden" name="group-0-INITIAL_FORMS" value="4">
            <input type="hidden" name="group-0-MIN_NUM_FORMS" value="0">
            <input type="hidden" name="group-0-MAX_NUM_FORMS" value="10">
            <button id="add-checklist-item-group-0" type="button" data-action="w-formset#add">Add</button>
            <ul data-w-formset-target="forms">
              <li id="group-0-item-0-item" data-w-formset-target="child">
                <input id="group-0-item-0-detail" type="text" name="group-0-item-0">
                <input type="hidden" name="group-0-item-0-DELETE" data-w-formset-target="deleteInput">
                <button id="group-0-item-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
              <li id="group-0-item-1-item" data-w-formset-target="child">
                <input id="group-0-item-1-detail" type="text" name="group-0-item-1">
                <input type="hidden" name="group-0-item-1-DELETE" data-w-formset-target="deleteInput">
                <button id="group-0-item-1-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
              <li id="group-0-item-2-item" data-w-formset-target="child">
                <input id="group-0-item-2-detail" type="text" name="group-0-item-2">
                <input type="hidden" name="group-0-item-2-DELETE" data-w-formset-target="deleteInput">
                <button id="group-0-item-2-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
              <li id="group-0-item-3-item" data-w-formset-target="child">
                <input id="group-0-item-3-detail" type="text" name="group-0-item-3">
                <input type="hidden" name="group-0-item-3-DELETE" data-w-formset-target="deleteInput">
                <button id="group-0-item-3-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </ul>
            <template data-w-formset-target="template">
              <li id="group-0-item-__prefix__-item" data-w-formset-target="child">
                <input id="group-0-item-__prefix__-detail" type="text" name="group-0-item-__prefix__">
                <button id="group-0-item-__prefix__-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </template>
          </fieldset>
          <input type="hidden" name="group-0-DELETE" data-w-formset-target="deleteInput">
        </div>
        <div id="group-item-1" data-w-formset-target="child">
          <input type="hidden" name="group-1-DELETE" data-w-formset-target="deleteInput" data-test-comment="Intentionally first">
          <input type="email" name="group-1-email">
          <input type="text" name="group-1-name">
          <button id="group-1-delete-button" type="button" data-action="w-formset#delete">Delete</button>
          <fieldset id="group-1-checklist" data-controller="w-formset">
            <legend>Inner checklist</legend>
            <input type="hidden" name="group-1-TOTAL_FORMS" value="3" data-w-formset-target="totalFormsInput">
            <input type="hidden" name="group-1-INITIAL_FORMS" value="3">
            <input type="hidden" name="group-1-MIN_NUM_FORMS" value="0">
            <input type="hidden" name="group-1-MAX_NUM_FORMS" value="10">
            <button id="add-checklist-item-group-1" type="button" data-action="w-formset#add">Add</button>
            <ul data-w-formset-target="forms">
              <li id="group-1-item-0-item" data-w-formset-target="child">
                <input id="group-1-item-0-detail" type="text" name="group-1-item-0">
                <input type="hidden" name="group-1-item-0-DELETE" data-w-formset-target="deleteInput">
                <button id="group-1-item-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
              <li id="group-1-item-0-item" data-w-formset-target="child">
                <input id="group-1-item-1-detail" type="text" name="group-1-item-1">
                <input type="hidden" name="group-1-item-1-DELETE" data-w-formset-target="deleteInput">
                <button id="group-1-item-1-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
              <li id="group-1-item-0-item" data-w-formset-target="child">
                <input id="group-1-item-2-detail" type="text" name="group-1-item-2">
                <input type="hidden" name="group-1-item-2-DELETE" data-w-formset-target="deleteInput">
                <button id="group-1-item-2-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </ul>
            <template data-w-formset-target="template">
              <li id="group-1-item-__prefix__-item" data-w-formset-target="child">
                <input id="group-1-item-__prefix__-detail" type="text" name="group-1-item-__prefix__">
                <button id="group-1-item-__prefix__-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </template>
          </fieldset>
        </div>
      </section>
      <button id="add-section" type="button" data-action="w-formset#add">Add</button>
      <template data-w-formset-target="template">
        <div id="group-item-__prefix__" data-w-formset-target="child">
          <input type="hidden" name="group-__prefix__-DELETE" data-w-formset-target="deleteInput">
          <input type="email" name="group-__prefix__-email">
          <input type="text" name="group-__prefix__-name">
          <button id="group-__prefix__-delete-button" type="button" data-action="w-formset#delete">Delete</button>
          <fieldset id="group-__prefix__-checklist" data-controller="w-formset">
            <legend>Inner checklist</legend>
            <input type="hidden" name="group-__prefix__-TOTAL_FORMS" value="1" data-w-formset-target="totalFormsInput">
            <input type="hidden" name="group-__prefix__-INITIAL_FORMS" value="1">
            <input type="hidden" name="group-__prefix__-MIN_NUM_FORMS" value="0">
            <input type="hidden" name="group-__prefix__-MAX_NUM_FORMS" value="10">
            <button id="add-checklist-item-group-__prefix__" type="button" data-action="w-formset#add">Add</button>
            <ul data-w-formset-target="forms">
              <li id="group-__prefix__-item-0-item" data-w-formset-target="child">
                <input id="group-__prefix__-item-0-detail" type="text" name="group-__prefix__-item-0">
                <input type="hidden" name="group-__prefix__-item-0-DELETE" data-w-formset-target="deleteInput">
                <button id="group-__prefix__-item-0-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </ul>
            <template data-w-formset-target="template">
              <li id="group-__prefix__-item-__prefix__-item" data-w-formset-target="child">
                <input id="group-__prefix__-item-__prefix__-detail" type="text" name="group-__prefix__-item-__prefix__">
                <input type="hidden" name="group-__prefix__-item-__prefix__-DELETE" data-w-formset-target="deleteInput">
                <button id="group-__prefix__-item-__prefix__-delete-button" type="button" data-action="w-formset#delete">Delete</button>
              </li>
            </template>
          </fieldset>
        </div>
      </template>
    </form>`;
    }
  });
});
