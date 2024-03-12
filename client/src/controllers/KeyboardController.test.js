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
    HTMLButtonElement.prototype.click = buttonClickMock;
  });

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('basic keyboard shortcut usage', () => {
    it('should call the click event when the `j` key is pressed after being registered', async () => {
      expect(buttonClickMock).not.toHaveBeenCalled();

      await setup(
        `<button id="btn" data-controller="w-kbd" data-w-kbd-key-value="j">Go</button>`,
      );

      // Simulate the keydown event & check that the default was prevented
      expect(simulateKey({ keyCode: 'j' })).toHaveProperty('keypress', false);

      expect(buttonClickMock).toHaveBeenCalledTimes(1);
      expect(buttonClickMock.mock.contexts).toEqual([
        document.getElementById('btn'),
      ]);
    });
  });
});
