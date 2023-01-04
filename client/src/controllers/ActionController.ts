import { Controller } from '@hotwired/stimulus';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 *
 * @example
 * <button
 *  type="submit"
 *  class="button no"
 *  data-controller="w-action"
 *  data-action="w-action#post"
 *  data-w-action-url-value='url/to/post/to'
 * >
 *  Enable
 * </button>
 */
export class ActionController extends Controller {
  static values = {
    continue: { type: Boolean, default: false },
    url: String,
  };

  continueValue: boolean;
  urlValue: string;

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
