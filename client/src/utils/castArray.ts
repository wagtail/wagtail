/**
 * Converts the provided args or single argument to an array.
 * Even if not originally supplied as one.
 */
export const castArray = (...args) => args.flat(1);
