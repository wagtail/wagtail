/**
 * Creates an array of numbers progressing from start up to, but not including, end.
 */
export const range = (min = 0, max = 0) =>
  [...Array(max - min).keys()].map((i) => i + min);
