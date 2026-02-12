import { setOptionalInterval } from './interval';

jest.useFakeTimers();
jest.spyOn(global, 'setInterval');

describe('setOptionalInterval', () => {
  afterEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  it('should be a pass-through for setInterval in normal cases', () => {
    const callback = jest.fn();
    const interval = setOptionalInterval(callback, 1);

    expect(setInterval).toHaveBeenCalledWith(callback, 1);
    expect(interval).toEqual(global.setInterval.mock.results[0].value);

    expect(callback).not.toHaveBeenCalled();
    jest.advanceTimersByTime(1);
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should not set the interval if the delay is unset', () => {
    const callback = jest.fn();
    const interval = setOptionalInterval(callback);

    expect(setInterval).not.toHaveBeenCalled();
    expect(interval).toBeNull();

    expect(callback).not.toHaveBeenCalled();
    jest.advanceTimersByTime(100);
    expect(callback).not.toHaveBeenCalled();
  });

  it('should not set the interval if the delay is set to 0', () => {
    const callback = jest.fn();
    const interval = setOptionalInterval(callback, 0);

    expect(setInterval).not.toHaveBeenCalled();
    expect(interval).toBeNull();

    expect(callback).not.toHaveBeenCalled();
    jest.advanceTimersByTime(100);
    expect(callback).not.toHaveBeenCalled();
  });

  it('should not set the interval if the delay is set to a very large value', () => {
    const callback = jest.fn();
    const interval = setOptionalInterval(callback, 9999999999);

    expect(setInterval).not.toHaveBeenCalled();
    expect(interval).toBeNull();

    expect(callback).not.toHaveBeenCalled();
    jest.advanceTimersByTime(10000000000);
    expect(callback).not.toHaveBeenCalled();
  });
});
