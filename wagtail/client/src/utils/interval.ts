/**
 * Like `setInterval`, but only sets the interval if the `delay` value is positive.
 *
 * Browsers treat non-positive `delay` values as 0, which means the interval will
 * run immediately (basically all the time). Instead of allowing this behavior,
 * this function will not set the interval instead. This allows the interval to
 * be disabled by setting the `delay` value to <= 0 (or a large enough value that
 * it overflows to negative), which is useful for user-configurable intervals.
 *
 * @param func the callback function to call
 * @param delay the interval delay in milliseconds
 * @param args the arguments to pass to the callback function
 * @returns the interval ID if the interval is valid, otherwise null
 */
export const setOptionalInterval = (
  func: TimerHandler,
  delay?: number,
  ...args: any[]
) => {
  // "The `delay` argument is converted to a signed 32-bit integer."
  // https://developer.mozilla.org/en-US/docs/Web/API/setInterval#return_value
  if (!delay || delay <= 0 || delay >= 2 ** 31) return null;
  return setInterval(func, delay, ...args);
};
