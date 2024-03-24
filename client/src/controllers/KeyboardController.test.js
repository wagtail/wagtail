import { Application } from '@hotwired/stimulus';
import { KeyboardController } from './KeyboardController';

describe('KeyboardController', () => {
  let app;
  const buttonClickMock = jest.fn();

  /**
   * Simulates a keydown, keypress, and keyup event for the provided key.
   */
  const simulateKey = (
    { key, which = key.charCodeAt(0), ctrlKey = false, metaKey = false },
    target = document.body,
  ) =>
    Object.fromEntries(
      ['keydown', 'keypress', 'keyup'].map((type) => [
        type,
        target.dispatchEvent(
          new KeyboardEvent(type, {
            bubbles: true,
            cancelable: true,
            key: key,
            which,
            ctrlKey,
            metaKey,
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
      expect(simulateKey({ key: 'j' })).toHaveProperty('keypress', false);

      expect(buttonClickMock).toHaveBeenCalledTimes(1);
      expect(buttonClickMock.mock.contexts).toEqual([
        document.getElementById('btn'),
      ]);
    });

    it('should call the click event when `ctrl+j` is pressed after being registered', async () => {
      expect(buttonClickMock).not.toHaveBeenCalled();

      await setup(
        `<button id="btn" data-controller="w-kbd" data-w-kbd-key-value="ctrl+j">Go</button>`,
      );

      // // Simulate the keydown event
      simulateKey({ key: 'j', which: 74, ctrlKey: true });

      expect(buttonClickMock).toHaveBeenCalledTimes(1);
      expect(buttonClickMock.mock.contexts).toEqual([
        document.getElementById('btn'),
      ]);
    });

    it('should call the click event when `command+j` is pressed after being registered', async () => {
      expect(buttonClickMock).not.toHaveBeenCalled();

      await setup(
        `<button id="btn" data-controller="w-kbd" data-w-kbd-key-value="command+j">Go</button>`,
      );

      // // Simulate the keydown event
      simulateKey({ key: 'j', which: 74, metaKey: true });

      expect(buttonClickMock).toHaveBeenCalledTimes(1);
      expect(buttonClickMock.mock.contexts).toEqual([
        document.getElementById('btn'),
      ]);
    });

    it('should call the click event when `mod+j` is pressed after being registered', async () => {
      expect(buttonClickMock).not.toHaveBeenCalled();

      await setup(
        `<button id="btn" data-controller="w-kbd" data-w-kbd-key-value="mod+j">Go</button>`,
      );

      // // Simulate the keydown event
      simulateKey({ key: 'j', which: 74, metaKey: true });
      simulateKey({ key: 'j', which: 74, ctrlKey: true });
      expect(buttonClickMock).toHaveBeenCalledTimes(3);
    });
  });

  describe('aria keyshortcuts usage', () => {
    it('should take the aria-keyshortcut attribute if the data-w-kbd-key-value is not set', async () => {
      expect(buttonClickMock).not.toHaveBeenCalled();

      await setup(
        `<button id="btn" data-controller="w-kbd" aria-keyshortcut="j">Go</button>`,
      );

      // Simulate the keydown event
      simulateKey({ key: 'j' });

      expect(buttonClickMock).toHaveBeenCalledTimes(1);
    });
  });
});
