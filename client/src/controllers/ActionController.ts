import { Controller } from '@hotwired/stimulus';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

/**
 * <button type="submit" class="button no"
 * data-controller="w-action"
 * data-action="click->w-action#post"
 * data-w-action-redirect-value="true"
 * data-w-action-redirect-url-value="{% url 'wagtailadmin_home' %}"
 * data-w-action-url-value = '{{ view.get_enable_url }}'>Enable</button>
 */
export class ActionController extends Controller {
  static values = {
    redirect: String,
    redirectUrl: String,
    url: String,
  };

  urlValue!: string;
  redirectValue!: any;
  redirectUrlValue!: string;

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

    if (this.redirectValue) {
      const nextElement = document.createElement('input');
      nextElement.type = 'hidden';
      nextElement.name = 'next';
      nextElement.value =
        this.redirectValue === 'false'
          ? window.location.href
          : this.redirectUrlValue;
      formElement.appendChild(nextElement);
    }

    document.body.appendChild(formElement);
    formElement.submit();
  }
}
