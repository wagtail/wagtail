import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

export class KeyboardController extends Controller<HTMLButtonElement> {
  static values = { key: { default: '', type: String } };

  handleKey(event: Event) {
    event.preventDefault();
    this.element.click();
  }

  initialize() {
    this.handleKey = this.handleKey.bind(this);
  }

  keyValueChanged(key, previousKey) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey, this.handleKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
