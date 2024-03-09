import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

export default class extends Controller {
  static values = { key: String };

  declare keyValue: string;

  handleKey(event: Event) {
    event.preventDefault();
    this.element.click();
  }

  connect() {
    Mousetrap.bind(this.keyValue, this.handleKey.bind(this));
  }

  disconnect() {
    Mousetrap.unbind(this.keyValue);
  }

  keyValueChanged(key, previousKey) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey, this.handleKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
