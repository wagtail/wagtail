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
 */
export class ActionController extends Controller<
  HTMLButtonElement | HTMLInputElement
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
}
