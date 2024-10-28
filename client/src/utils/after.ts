/**
 * Creates a function that invokes `func` once it's called `count` or more times.
 *
 * @see https://github.com/lodash/lodash/blob/4.17.15/lodash.js#L9990
 */
export const after = (func, count: number = 0) => {
  if (typeof func !== 'function') throw new TypeError('Must be a function.');

  let remainingCalls =
    Number.isFinite(count) && Number.isInteger(count) ? count : 0;

  return (...args) => {
    const result = remainingCalls < 1 ? func.apply(this, args) : null;
    remainingCalls -= 1;
    return result;
  };
};
