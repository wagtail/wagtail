import { Controller } from '@hotwired/stimulus';

/**
 * Adds the ability for a field to trigger an automatic submission of its attached form.
 *
 * @example - Once any change is made to the below select field, the form will be auto submitted
 * ```html
 * <form>
 *   <select name="order" data-controller="w-submit" data-action="change->w-submit#submit">
 *     <option value="A-Z">A to Z</option>
 *     <option value="Z-A">Z to A</option>
 *   </select>
 * </form>
 * ```
 */
export class SubmitController extends Controller<
  HTMLInputElement | HTMLSelectElement
> {
  submit() {
    const form = this.element.form;

    if (!form) {
      throw new Error(
        `${this.identifier} controlled element must be part of a <form />`,
      );
    }

    if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }
}
