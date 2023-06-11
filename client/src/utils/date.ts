/**
 * Compare two date objects. Ignore minutes and seconds.
 */
export const isDateEqual = (x: Date, y: Date) =>
  x &&
  y &&
  x.getDate() === y.getDate() &&
  x.getMonth() === y.getMonth() &&
  x.getFullYear() === y.getFullYear();
