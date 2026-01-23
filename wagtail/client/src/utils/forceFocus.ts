import { debounce } from './debounce';

/**
 * Trigger a focus on a potentially non-focusable element, awaiting
 * for any delays in DOM creation. Smoothly scroll to the element
 * if it is not already in view, then trigger a DOM focus.
 *
 * Once the target element loses focus, the `tabindex` attribute,
 * if it was added, remove the attribute.
 *
 * @example
 * ```ts
 * forceFocus(document.getElementById('my-element') as HTMLElement);
 * ```
 */
export const forceFocus = debounce(
  (
    element: HTMLElement | SVGElement,
    { preventScroll = false }: FocusOptions = {},
  ) => {
    if (!element.hasAttribute('tabindex')) {
      const handleBlur = () => {
        element.removeAttribute('tabindex');
        element.removeEventListener('blur', handleBlur);
        element.removeEventListener('focusout', handleBlur);
      };

      element.setAttribute('tabindex', '-1');
      element.addEventListener('blur', handleBlur);
      element.addEventListener('focusout', handleBlur);
    }

    if (!preventScroll) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    element.focus({ preventScroll });
  },
  50,
);
