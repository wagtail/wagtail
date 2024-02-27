import { Application } from '@hotwired/stimulus';

import { OrderableController } from './OrderableController';

jest.useFakeTimers();

describe('OrderableController', () => {
  const eventNames = ['w-orderable:ready', 'w-messages:add'];

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
    html = `
  <form>
    <input name="csrfmiddlewaretoken" value="__MOCK_CSRF__" />
    <ul
      class="orderable"
      id="orderable"
      data-controller="w-orderable"
      data-w-orderable-active-class="is-active"
      data-w-orderable-message-value="'__LABEL__' has been updated!"
      data-w-orderable-url-value="/base/url/999999"
    >
      <li id="item-73" data-w-orderable-target="item" data-w-orderable-item-id="73" data-w-orderable-item-label="Beef">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keydown.up->w-orderable#up:prevent keydown.down->w-orderable#down:prevent keydown.enter->w-orderable#apply">--</button>
        Item 73
      </li>
      <li id="item-75" data-w-orderable-target="item" data-w-orderable-item-id="75" data-w-orderable-item-label="Cheese">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keydown.up->w-orderable#up:prevent keydown.down->w-orderable#down:prevent keydown.enter->w-orderable#apply">--</button>
        Item 75
      </li>
      <li id="item-93" data-w-orderable-target="item" data-w-orderable-item-id="93" data-w-orderable-item-label="Santa">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keydown.up->w-orderable#up:prevent keydown.down->w-orderable#down:prevent keydown.enter->w-orderable#apply">--</button>
        Item 93
      </li>
    </ul>
  </form>`,
    identifier = 'w-orderable',
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = new Application();

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    application.register(identifier, OrderableController);

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
    jest.clearAllMocks();
  });

  describe('base behavior', () => {
    it('should dispatch a ready event', async () => {
      expect(events['w-orderable:ready']).toHaveLength(0);

      await setup();

      expect(events['w-orderable:ready']).toHaveLength(1);

      expect(events['w-orderable:ready'][0]).toHaveProperty('detail', {
        order: ['73', '75', '93'],
      });
    });

    it('should destroy the sortable instance on disconnect', async () => {
      const [controller] = await setup();

      expect(controller.sortable).toBeInstanceOf(Object);

      const spy = jest.spyOn(controller.sortable, 'destroy');

      await Promise.resolve(
        document.getElementById('orderable').removeAttribute('data-controller'),
      );

      expect(spy).toHaveBeenCalled();
    });
  });

  /**
   * To avoid the complexity of mocking drag & drop in JSDOM/Jest - simply confirm the options
   */
  describe('using sortable.js library with the correct options', () => {
    it('should set up callbacks to support drag & drop', async () => {
      const [controller] = await setup();

      expect([...document.getElementById('orderable').classList]).toEqual([
        'orderable',
      ]);

      // emulate a drag start
      controller.sortable.options.onStart();

      // it should set the active class
      expect([...document.getElementById('orderable').classList]).toEqual([
        'orderable',
        'is-active',
      ]);

      const item = document.querySelector('li:first-of-type');

      // emulate a drag end (no change)
      controller.sortable.options.onEnd({ item, oldIndex: 0, newIndex: 0 });

      expect(global.fetch).not.toHaveBeenCalled();

      // it should remove the active class
      expect([...document.getElementById('orderable').classList]).toEqual([
        'orderable',
      ]);

      fetch.mockResponseSuccessJSON('');

      // emulate a drag end (with change)

      controller.sortable.options.onEnd({ item, oldIndex: 0, newIndex: 2 });

      expect(global.fetch).toHaveBeenCalledWith('/base/url/73?position=2', {
        body: expect.any(Object),
        method: 'POST',
      });
    });

    it('should set up the correct data attribute references for sortable.js', async () => {
      const [controller] = await setup();

      expect(controller.sortable.options).toEqual(
        expect.objectContaining({
          dataIdAttr: 'data-w-orderable-item-id',
          draggable: '[data-w-orderable-target="item"]',
          handle: '[data-w-orderable-target="handle"]',
        }),
      );

      const [controllerWithDifferentIdentifier] = await setup(
        `<ul id="orderable" data-controller="w-something"></ul>`,
        'w-something',
      );

      expect(controllerWithDifferentIdentifier.sortable.options).toEqual(
        expect.objectContaining({
          dataIdAttr: 'data-w-something-item-id',
          draggable: '[data-w-something-target="item"]',
          handle: '[data-w-something-target="handle"]',
        }),
      );
    });

    it('should set up the classes', async () => {
      const [controller] = await setup(
        `<ul
          id="orderable"
          data-controller="w-orderable"
          data-w-orderable-chosen-class="is-chosen"
          data-w-orderable-drag-class="is-dragging"
          data-w-orderable-ghost-class="is-ghost"
          >
        </ul>`,
      );

      expect(controller.sortable.options).toEqual(
        expect.objectContaining({
          chosenClass: 'is-chosen',
          dragClass: 'is-dragging',
          ghostClass: 'is-ghost',
        }),
      );
    });
  });

  describe('manually moving', () => {
    const UP = ['keydown', { key: 'ArrowUp', keyCode: 38 }];
    const DOWN = ['keydown', { key: 'ArrowDown', keyCode: 40 }];
    const ENTER = ['keydown', { key: 'Enter', keyCode: 13 }];

    it('should support moving to another position', async () => {
      const [controller] = await setup();

      expect(controller.sortable).toBeInstanceOf(Object);
      expect(controller.order).toEqual(['73', '75', '93']);
      expect(document.activeElement).toEqual(document.body);

      const sortSpy = jest.spyOn(controller.sortable, 'sort');

      const handle = document.querySelector('#item-75 button.handle');

      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...DOWN)));

      expect(sortSpy).toHaveBeenLastCalledWith(['73', '93', '75'], true);
      expect(document.activeElement).toEqual(handle); // keep focus on the handle (after move)

      // it should not error when moving down beyond the last element

      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...DOWN)));

      expect(sortSpy).toHaveBeenLastCalledWith(['73', '93', '75'], true);
      expect(document.activeElement).toEqual(handle); // keep focus on the handle (after move)

      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...UP)));
      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...UP)));
      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...UP)));

      expect(sortSpy).toHaveBeenLastCalledWith(['75', '73', '93'], true);
    });

    it('should allow applying a manually re-ordered item', async () => {
      const [controller] = await setup();

      expect(events['w-messages:add']).toHaveLength(0);
      expect(controller.sortable).toBeInstanceOf(Object);
      expect(controller.order).toEqual(['73', '75', '93']);
      expect(global.fetch).not.toHaveBeenCalled();

      const handle = document.querySelector('#item-93 button.handle');

      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...UP)));

      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseSuccessJSON('');

      await Promise.resolve(handle.dispatchEvent(new KeyboardEvent(...ENTER)));

      expect(global.fetch).toHaveBeenCalledWith('/base/url/93?position=1', {
        body: expect.any(FormData),
        method: 'POST',
      });

      expect(
        global.fetch.mock.calls[0][1].body.get('csrfmiddlewaretoken'),
      ).toEqual('__MOCK_CSRF__');

      await Promise.resolve();

      expect(events['w-messages:add']).toHaveLength(1);
      expect(events['w-messages:add'][0]).toHaveProperty('detail', {
        clear: true,
        text: "'Santa' has been updated!",
        type: 'success',
      });
    });
  });
});
