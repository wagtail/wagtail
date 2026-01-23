import { debounce } from './debounce';

jest.useFakeTimers();
jest.spyOn(global, 'clearTimeout');
jest.spyOn(global, 'setTimeout');

describe('debounce', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should delay the debounced function', async () => {
    const func = jest.fn();

    const debounced = debounce(func, 320);
    expect(func).toHaveBeenCalledTimes(0);
    expect(setTimeout).not.toHaveBeenCalled();

    debounced();
    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 320);

    await jest.runAllTimersAsync();
    expect(func).toHaveBeenCalledTimes(1);
  });

  it('should call the provided function only once when called multiple times within the delay', async () => {
    const func = jest.fn();

    const debounced = debounce(func, 320);
    expect(func).toHaveBeenCalledTimes(0);
    expect(setTimeout).not.toHaveBeenCalled();

    debounced();
    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 320);
    debounced();
    debounced();

    await jest.runAllTimersAsync();
    expect(func).toHaveBeenCalledTimes(1);
  });

  it('should provide a way to cancel any pending calls', async () => {
    const func = jest.fn();

    const debounced = debounce(func, 600);

    debounced();
    debounced.cancel();

    expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 600);
    expect(clearTimeout).toHaveBeenLastCalledWith(expect.any(Number));
    await jest.runAllTimersAsync();
    expect(func).toHaveBeenCalledTimes(0);
  });

  it('should not delay if wait is not a number', () => {
    const func = jest.fn();

    debounce(func, false)();
    expect(func).toHaveBeenCalledTimes(1);

    debounce(func, null)();
    expect(func).toHaveBeenCalledTimes(2);

    debounce(func, '')();
    expect(func).toHaveBeenCalledTimes(3);

    debounce(func, 0 / 0 /* NaN */)();
    expect(func).toHaveBeenCalledTimes(4);
  });

  it('should provide the args to the function', async () => {
    const func = jest.fn();

    debounce(func, null)('a', 'b', 'c');
    expect(func).toHaveBeenCalledTimes(1);
    expect(func).toHaveBeenCalledWith('a', 'b', 'c');

    debounce(func, 30)('x', 'y', ['Z']);
    expect(func).toHaveBeenCalledTimes(1);

    await jest.runAllTimersAsync();
    expect(func).toHaveBeenCalledTimes(2);
    expect(func).toHaveBeenLastCalledWith('x', 'y', ['Z']);
  });

  it('should return a promise when the debounced function is called (using wait value)', () => {
    const func = jest.fn((prefix = '_') => `${prefix}:bar`);
    const debounced = debounce(func, 100);
    const promise = debounced('foo');

    expect(promise).toBeInstanceOf(Promise);
    expect(func).toHaveBeenCalledTimes(0);

    jest.runAllTimers();
    expect(func).toHaveBeenCalledTimes(1);

    return expect(promise).resolves.toBe('foo:bar');
  });

  it('should return a promise when the debounced function is called (when resolved immediately, using a falsey value)', () => {
    const func = jest.fn((prefix = '_') => `${prefix}:bar`);
    const debounced = debounce(func, null);
    const promise = debounced();

    expect(promise).toBeInstanceOf(Promise);
    expect(func).toHaveBeenCalledTimes(1);

    return expect(promise).resolves.toBe('_:bar');
  });

  it('should reject the promise if the function throws (when delayed)', () => {
    const func = jest.fn(() => {
      throw new Error('some-error');
    });
    const debounced = debounce(func, 500);

    const promise = debounced();

    expect(promise).toBeInstanceOf(Promise);

    expect(func).toHaveBeenCalledTimes(0);

    jest.runAllTimers();

    expect(func).toHaveBeenCalledTimes(1);

    return expect(promise).rejects.toThrow('some-error');
  });

  it('should reject the promise if the function throws (when immediately run)', () => {
    const func = jest.fn(() => {
      throw new Error('some-error');
    });

    const debounced = debounce(func, false);

    const promise = debounced();

    expect(promise).toBeInstanceOf(Promise);

    return expect(promise).rejects.toThrow('some-error');
  });
});
