import { Controller } from '@hotwired/stimulus';
import autosize from 'autosize';

export class AutoSizeController extends Controller {
  static targets = ['input'];

  connect() {
    autosize(this.element);
  }

  disconnect() {
    autosize.destroy(this.element);
  }

}
