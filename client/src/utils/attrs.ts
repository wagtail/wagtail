/**
 * Sets attributes on a given HTML element.
 * @param element HTMLElement to set attributes on
 * @param attrs An object containing key-value pairs of attributes to set
 */
export function setAttrs(
  element: HTMLElement,
  attrs: Record<string, string | boolean | number>,
): void {
  Object.entries(attrs).forEach(([key, value]) => {
    element.setAttribute(key, `${value}`);
  });
}
