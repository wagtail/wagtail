import Mousetrap from 'mousetrap';

import initKeyboardShortcuts from './initKeyboardShortcuts';

describe('initKeyboardShortcuts', () => {
  beforeAll(() => {
    document.body.innerHTML = `
    <div>
      <span id="username" />
      <button id="button" data-keyboard-shortcut="mod+s" />
    </div>`;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('should use Mousetrap to bind a keyboard shortcut to element with data attribute', () => {
    const preventDefault = jest.fn();
    const clickMock = jest.fn();
    const button = document.getElementById('button');
    button.addEventListener('click', clickMock);

    expect(clickMock).not.toHaveBeenCalled();
    expect(Mousetrap.bind).not.toHaveBeenCalled();

    initKeyboardShortcuts();

    expect(Mousetrap.bind).toHaveBeenCalledTimes(1);
    expect(Mousetrap.bind).toHaveBeenCalledWith(
      ['mod+s'],
      expect.any(Function),
    );

    // call bind handler
    Mousetrap.bind.mock.calls[0][1]({ preventDefault });
    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(clickMock).toHaveBeenCalledTimes(1);
  });

  it('should allow registration of a keyboard shortcut via dispatching an event', () => {
    expect(Mousetrap.bind).not.toHaveBeenCalled();

    const callback = jest.fn();

    document.dispatchEvent(
      new CustomEvent('wagtail:bind-keyboard-shortcut', {
        detail: {
          callback,
          key: '/',
          target: document.getElementById('button'),
        },
      }),
    );

    expect(Mousetrap.bind).toHaveBeenCalledTimes(1);
    expect(Mousetrap.bind).toHaveBeenCalledWith(['/'], expect.any(Function));
    Mousetrap.bind.mock.calls[0][1]({});
    expect(callback).toHaveBeenCalledTimes(1);
  });
});
