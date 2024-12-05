import { transition } from './transition';

jest.useFakeTimers();

describe('transition', () => {
  beforeAll(() => {
    document.body.innerHTML = `<main id="main"></main>`;
  });

  it('should resolve the immediately if maxDelay is 0 or falsy', async () => {
    expect(
      await transition(document.getElementById('main'), { maxDelay: 0 }),
    ).toBe(null);

    expect(
      await transition(document.getElementById('main'), { maxDelay: false }),
    ).toBe(null);

    expect(
      await transition(document.getElementById('main'), { maxDelay: -1 }),
    ).toBe(null);
  });

  it('should resolve after the maxDelay (350ms) if no events are fired', async () => {
    const resolve = jest.fn();

    transition(document.getElementById('main')).then(resolve);

    await jest.advanceTimersByTimeAsync(200);

    expect(resolve).not.toHaveBeenCalled();

    await jest.advanceTimersByTimeAsync(149);

    expect(resolve).not.toHaveBeenCalled();

    await jest.advanceTimersByTimeAsync(1);

    expect(resolve).toHaveBeenCalledWith(null);
  });

  it('should resolve if transitionend or animationend is fired', async () => {
    const resolve = jest.fn();

    transition(document.getElementById('main')).then(resolve);

    await jest.advanceTimersByTimeAsync(200);

    expect(resolve).not.toHaveBeenCalled();

    const event = new Event('transitionend', {
      bubbles: true,
      cancelable: false,
    });

    document.getElementById('main').dispatchEvent(event);

    await jest.advanceTimersByTimeAsync(0);

    expect(resolve).toHaveBeenCalledWith(event);
  });

  it('should resolve if animationend is fired', async () => {
    const resolve = jest.fn();

    transition(document.getElementById('main')).then(resolve);

    await jest.advanceTimersByTimeAsync(200);

    expect(resolve).not.toHaveBeenCalled();

    const event = new Event('animationend', {
      bubbles: true,
      cancelable: false,
    });

    document.getElementById('main').dispatchEvent(event);

    await jest.advanceTimersByTimeAsync(0);

    expect(resolve).toHaveBeenCalledWith(event);
  });
});
