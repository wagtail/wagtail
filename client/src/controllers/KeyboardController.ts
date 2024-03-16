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
export class KeyboardController extends Controller<
  HTMLButtonElement | HTMLAnchorElement
> {
  static values = { key: { default: '', type: String } };
  declare keyValue: string;

  handleKey(event: Event) {
    if (event.preventDefault) event.preventDefault();
    this.element.click();
  }

  initialize() {
    this.handleKey = this.handleKey.bind(this);
    if (!this.keyValue && this.element.ariaKeyShortcuts) {
      this.keyValue = this.element.ariaKeyShortcuts;
    }
  }

  /**
   * When a key is set or changed, bind the handler to the keyboard shortcut. This will override the shortcut, if already set, https://craig.is/killing/mice#:~:text=if%20you%20bind%20the%20same,original%20callback%20you%20had%20specified.
   */

  keyValueChanged(key, previousKey) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
