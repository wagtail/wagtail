/**
 * Escapes provided HTML.
 *
 * https://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
 *
 * @param {string} unsafe - raw HTML to be made safe
 * @returns {string}
 */
export function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
