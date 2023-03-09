import { Controller } from '@hotwired/stimulus';
import autosize from 'autosize';

export class AutoSizeController extends Controller {
  connect() {
    autosize(this.element);
    this.element.addEventListener('input', () => {
      autosize.update(this.element);
    });
  }

  disconnect() {
    autosize.destroy(this.element);
    this.element.removeEventListener('input', () => {
      autosize.update(this.element);
    });
  }
}
