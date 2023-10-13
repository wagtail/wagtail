import { Controller } from '@hotwired/stimulus';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * Adds the ability for an element to activate a discrete action
 * such as clicking the button dynamically from some other event or
 * triggering a form submission where the form is created dynamically
 * in the DOM and then submitted.
 *
 * @example - triggering a click
 * <button
 *  type="button"
 *  data-controller="w-action"
 *  data-action="some-event#click"
 * >
 *  Go
 * </button>
 *
 * @example - triggering a dynamic POST submission
 * <button
 *  type="submit"
 *  data-controller="w-action"
 *  data-action="w-action#post"
 *  data-w-action-url-value='url/to/post/to'
 * >
 *  Enable
 * </button>
 *
 * @example - triggering a dynamic redirect
 * // note: a link is preferred normally
 * <form>
 *   <select name="url" data-controller="w-action" data-action="change->w-action#redirect">
 *     <option value="/path/to/1">1</option>
 *     <option value="/path/to/2">2</option>
 *   </select>
 * </form>
 *
 * @example - triggering selection of the text in a field
 * <form>
 *   <textarea name="url" data-controller="w-action" data-action="click->w-action#select">
 *     This text will all be selected on focus.
 *   </textarea>
 * </form>
 */
export class ActionController extends Controller<
  HTMLButtonElement | HTMLInputElement | HTMLTextAreaElement
> {
  static values = {
    continue: { type: Boolean, default: false },
    url: String,
  };

  declare continueValue: boolean;
  declare urlValue: string;

  click() {
    this.element.click();
  }

  post(event: Event) {
    event.preventDefault();
    event.stopPropagation();

    const formElement = document.createElement('form');

    formElement.action = this.urlValue;
    formElement.method = 'POST';

    const csrftokenElement = document.createElement('input');
    csrftokenElement.type = 'hidden';
    csrftokenElement.name = 'csrfmiddlewaretoken';
    csrftokenElement.value = WAGTAIL_CONFIG.CSRF_TOKEN;
    formElement.appendChild(csrftokenElement);

    /** If continue is false, pass the current URL as the next param
     * so that the user is redirected back to the current page instead
     * of continuing to the submitted page */
    if (!this.continueValue) {
      const nextElement = document.createElement('input');
      nextElement.type = 'hidden';
      nextElement.name = 'next';
      nextElement.value = window.location.href;
      formElement.appendChild(nextElement);
    }

    document.body.appendChild(formElement);
    formElement.submit();
  }

  /**
   * Trigger a redirect based on the custom event's detail, the Stimulus param
   * or finally check the controlled element for a value to use.
   */
  redirect(
    event: CustomEvent<{ url?: string }> & { params?: { url?: string } },
  ) {
    const url = event?.params?.url ?? event?.detail?.url ?? this.element.value;
    if (!url) return;
    window.location.assign(url);
  }

  /**
   * Select all the text in an input or textarea element.
   */
  select() {
    if (this.element instanceof HTMLButtonElement) return;
    this.element?.select();
  }

  /**
   * Reset the field to a supplied or the field's initial value (default).
   * Only update if the value to change to is different from the current value.
   */
  reset(
    event: CustomEvent<{ value?: string }> & { params?: { value?: string } },
  ) {
    const target = this.element;
    const currentValue = target.value;

    const { value: newValue = '' } = {
      value: target instanceof HTMLInputElement ? target.defaultValue : '',
      ...event?.params,
      ...event?.detail,
    };

    if (currentValue === newValue) return;

    target.value = newValue;
    this.dispatch('change', {
      bubbles: true,
      cancelable: false,
      prefix: '',
      target,
    });
  }
}
