import { Application } from '@hotwired/stimulus';
import { KeyboardController } from './KeyboardController';

describe('KeyboardController', () => {
  let app;
  const buttonClickMock = jest.fn();

  /**
   * Simulates a keydown, keypress, and keyup event for the provided key.
   */
  const simulateKey = (
    { keyCode, which = keyCode.charCodeAt(0) },
    target = document.body,
  ) =>
    Object.fromEntries(
      ['keydown', 'keypress', 'keyup'].map((type) => [
        type,
        target.dispatchEvent(
          new KeyboardEvent(type, {
            bubbles: true,
            cancelable: true,
            keyCode,
            which,
          }),
        ),
      ]),
    );

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    app = Application.start();
    app.register('w-kbd', KeyboardController);

    await Promise.resolve();
  };

  beforeAll(() => {
    delete window.location;

    window.location = Object.defineProperties(
      {},
      {
        ...Object.getOwnPropertyDescriptors(oldWindowLocation),
        assign: { configurable: true, value: jest.fn() },
      },
    );
  });

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('simulate keydown event', () => {
    beforeEach(async () => {
      await setup(`
            <button
              id="btn"
              class="button no"
              data-controller="w-kbd"
              data-w-kbd-key-value="mod+j"
            >
              Enable
            </button>`);
    });

    it('should call the click event', async () => {
      const button = document.getElementById('btn');
      button.addEventListener('click', () => {});
      const clickMock = jest.fn();
      HTMLButtonElement.prototype.click = clickMock;

      expect(app.controllers.length).toBe(1);
      expect(button.getAttribute('data-w-kbd-key-value')).toBe('mod+j');
      expect(app.controllers[0].element).toBe(button);

      const keyDownEvent = new KeyboardEvent('keydown', {
        key: 'j',
        ctrlKey: true,
      });
      const isDispatched = document.dispatchEvent(keyDownEvent);

      expect(isDispatched).toBe(true);
      expect(clickMock).toHaveBeenCalled();
    });
  });
});
