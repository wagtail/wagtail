export function getOrDefault<K, V>(map: Map<K, V>, key: K, defaultValue: V) {
  const value = map.get(key);
  if (typeof value === 'undefined') {
    return defaultValue;
  }
  return value;
}
