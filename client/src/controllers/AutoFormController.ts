import { AbstractController } from './AbstractController';

/**
 * Adds ability for automatic form submission.
 *
 * @example
 * // once any change is made to the below select box, the form will be auto submitted
 * <form>
 *   <select name="order" data-controller="w-auto-form" data-action="change->w-auto-form#submit">
 *     <option value="A-Z">A to Z</option>
 *     <option value="Z-A">Z to A</option>
 *   </select>
 * </form>
 */
export class AutoFormController extends AbstractController<HTMLInputElement> {
  /**
   * Submit the Input's associated form, using the `requestSubmit` if supported
   * https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/requestSubmit
   *
   * Fall back to `submit` instead, if not supported.
   */
  submit() {
    const form = this.element.form;
    if (!form) return;

    if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }
}
