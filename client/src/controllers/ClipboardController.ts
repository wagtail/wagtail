import { Controller } from '@hotwired/stimulus';

type CopyOptions = {
  /** Custom supplied value to copy to the clipboard. */
  value?: string;
};

/**
 * Adds the ability for an element to copy the value from a target to the clipboard.
 *
 * @example
 * ```html
 * <div data-controller="w-clipboard">
 *   <input type="text" value="Hello World" data-w-clipboard-target="value" />
 *   <button type="button" data-action="w-clipboard#copy">Copy</button>
 * </div>
 * ```
 */
export class ClipboardController extends Controller<HTMLElement> {
  static targets = ['value'];

  declare readonly hasValueTarget: boolean;
  declare readonly valueTarget:
    | HTMLInputElement
    | HTMLTextAreaElement
    | HTMLSelectElement;

  /**
   * Copies the value from either the Custom Event detail, Stimulus action params or
   * the value target to the clipboard. If no value is found, nothing happens.
   * If the clipboard is not available an error event is dispatched and it will
   * intentionally fail silently.
   */
  copy(event: CustomEvent<CopyOptions> & { params?: CopyOptions }) {
    const {
      value = this.hasValueTarget
        ? this.valueTarget.value
        : (this.element as HTMLInputElement).value || null,
    } = { ...event.detail, ...event.params };

    if (!value) return;

    const copyEvent = this.dispatch('copy');

    if (copyEvent.defaultPrevented) return;

    new Promise((resolve, reject) => {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(value).then(resolve, reject);
      } else {
        reject();
      }
    })
      .then(() =>
        this.dispatch('copied', { detail: { clear: true, type: 'success' } }),
      )
      .catch(() =>
        this.dispatch('error', { detail: { clear: true, type: 'error' } }),
      );
  }
}
