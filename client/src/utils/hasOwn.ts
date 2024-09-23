/**
 * Returns true if the specified object has the
 * indicated property as its own property.
 */
const hasOwn = (object: Record<string, unknown>, key: string) =>
  object ? Object.prototype.hasOwnProperty.call(object, key) : false;

export { hasOwn };
