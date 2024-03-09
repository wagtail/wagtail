import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

export default class extends Controller {
  static values = { key: String };

  handleKey(event: Event) {
    event.preventDefault();
    this.element.click();
  }

  initialize(): void {
    this.handleKey = this.handleKey.bind(this);
  }

  keyValueChanged(key, previousKey) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey, this.handleKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
