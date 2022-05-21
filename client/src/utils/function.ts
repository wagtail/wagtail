/**
 * Useful generic toolkit functions.
 */

/**
 * Returns the value of the first argument. All others are ignored.
 *
 * @example
 * identity(7, 8, 9)
 * // 7
 */
const identity = <T extends any[]>(...args: T): T[0] => args[0];

/**
 * This method does nothing, returns `undefined`.
 */
// eslint-disable-next-line @typescript-eslint/no-empty-function
const noop = (): void => {};

export { identity, noop };
