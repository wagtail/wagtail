import { Controller } from '@hotwired/stimulus';

//  <button data-controller="w-action"
//  data-w-action-csrf-token-value = '{{ csrf_token|escapejs }}'
//  data-w-action-post-url-value = '{{ view.get_enable_url }}'
//  data-w-action-key-name-value = 'csrfmiddlewaretoken'
//  data-action="click->w-action#enableAction"
//  type="submit" class="button no">Enable</button>

export class ActionController extends Controller {
  static values = {
    csrfToken: String,
    postUrl: String,
    keyName: String,
  };

  csrfTokenValue!: string;
  postUrlValue!: string;
  keyNameValue!: string;

  enableAction(event: Event) {
    event.preventDefault();
    event.stopPropagation();

    const XHR = new XMLHttpRequest();
    const formData = new FormData();

    formData.append(this.keyNameValue, this.csrfTokenValue);

    XHR.addEventListener('load', () => {
      window.location.reload();
    });

    XHR.addEventListener('error', () => {
      throw new Error('oops something went wrong ');
    });

    XHR.open('POST', this.postUrlValue);

    XHR.send(formData);
  }
}
