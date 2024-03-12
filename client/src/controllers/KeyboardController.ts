import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

/**
 * Adds the ability to trigger a button click event using a keyboard shortcut
 * declared on the controlled element.
 *
 * @example
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key="[">Trigger me with the <kbd>[</kbd> key.</button>
 * ```
 */
export class KeyboardController extends Controller<HTMLButtonElement> {
  static values = { key: { default: '', type: String } };

  handleKey(event: Event) {
    if (event.preventDefault) event.preventDefault();
    this.element.click();
  }

  initialize() {
    this.handleKey = this.handleKey.bind(this);
  }

  keyValueChanged(key, previousKey) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
