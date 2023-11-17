import { Application } from '@hotwired/stimulus';

import { OrderableController } from './OrderableController';

jest.useFakeTimers();

describe('OrderableController', () => {
  const eventNames = ['w-orderable:ready'];

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
  <section>
    <ul
      data-controller="w-orderable"
      data-w-orderable-message-value="'__label__' has been updated!"
    >
      <li data-w-orderable-target="item" data-w-orderable-item-id="73" data-w-orderable-item-label="Beef">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keyup.up->w-orderable#up:prevent keyup.down->w-orderable#down:prevent keydown.enter->w-orderable#apply blur->w-orderable#apply">--</button>
        Item 73
      </li>
      <li data-w-orderable-target="item" data-w-orderable-item-id="75" data-w-orderable-item-label="Cheese">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keyup.up->w-orderable#up:prevent keyup.down->w-orderable#down:prevent keydown.enter->w-orderable#apply blur->w-orderable#apply">--</button>
        Item 75
      </li>
      <li data-w-orderable-target="item" data-w-orderable-item-id="93" data-w-orderable-item-label="Santa">
        <button class="handle" type="button" data-w-orderable-target="handle" data-action="keyup.up->w-orderable#up:prevent keyup.down->w-orderable#down:prevent keydown.enter->w-orderable#apply blur->w-orderable#apply">--</button>
        Item 93
      </li>
    </ul>
  </section>`,
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
  });

  describe('drag & drop', () => {
    it('should dispatch a ready event', async () => {
      expect(events['w-orderable:ready']).toHaveLength(0);

      await setup();

      expect(events['w-orderable:ready']).toHaveLength(1);

      expect(events['w-orderable:ready'][0]).toHaveProperty('detail', {
        order: ['73', '75', '93'],
      });
    });
  });
});
