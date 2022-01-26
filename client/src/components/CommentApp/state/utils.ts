export function update<T>(base: T, updatePartial: Partial<T>): T {
  return Object.assign(base, updatePartial);
}
