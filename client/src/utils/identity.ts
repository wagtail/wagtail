/**
 * Returns the value of the first argument. All others are ignored.
 *
 * @example
 * identity(7, 8, 9)
 * // 7
 */
const identity = <T extends any[]>(...args: T): T[0] => args[0];

export { identity };
