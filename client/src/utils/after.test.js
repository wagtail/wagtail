import { after } from './after';

describe('after', () => {
  it('should call the function after the specified number of calls', () => {
    const mockFn = jest.fn();
    const afterFn = after(mockFn, 1);

    afterFn();
    expect(mockFn).not.toHaveBeenCalled();

    afterFn();
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('should call the function every time after the specified number of calls', () => {
    const mockFn = jest.fn();
    const afterFn = after(mockFn, 2);

    afterFn();
    afterFn();
    expect(mockFn).not.toHaveBeenCalled();

    afterFn();
    afterFn();
    expect(mockFn).toHaveBeenCalledTimes(2);

    afterFn();
    expect(mockFn).toHaveBeenCalledTimes(3);
  });

  it('should not call the function if the number of calls is not reached', () => {
    const mockFn = jest.fn();
    const afterFn = after(mockFn, 5);

    afterFn();
    afterFn();
    afterFn();
    expect(mockFn).not.toHaveBeenCalled();
  });

  it('should default the count to zero', () => {
    const mockFn = jest.fn();
    const afterFn = after(mockFn);

    afterFn();
    expect(mockFn).toHaveBeenCalled();
  });

  it('should handle bad data for the count gracefully', () => {
    const mockFn = jest.fn();

    after(mockFn, '??')();
    after(mockFn, NaN)();
    after(mockFn, Infinity)();
    after(mockFn, undefined)();
    after(mockFn, null)();

    expect(mockFn).toHaveBeenCalledTimes(5);
  });

  it('should throw an error if a function is not provided', () => {
    expect(() => after(jest.fn())).not.toThrow();
    expect(() => after()).toThrow();
    expect(() => after(undefined)).toThrow();
    expect(() => after('')).toThrow();
  });
});
