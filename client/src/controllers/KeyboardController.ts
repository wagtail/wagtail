import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

/**
 * Adds the ability to trigger a button click event using a
 * keyboard shortcut declared on the controlled element.
 *
 * @see https://craig.is/killing/mice
 *
 * @example
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key="[">Trigger me with the <kbd>[</kbd> key.</button>
 * ```
 *
 * @example - use aria-keyshortcuts (when the key string is compatible with Mousetrap's syntax)
 * @see https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes/aria-keyshortcuts
 * ```html
 * <button type="button" data-controller="w-kbd" aria-keyshortcuts="alt+p">Trigger me with alt+p.</button>
 * ```
 */
export class KeyboardController extends Controller<
  HTMLButtonElement | HTMLAnchorElement
> {
  static values = { key: { default: '', type: String } };

  /** Keyboard shortcut string. */
  declare keyValue: string;

  initialize() {
    this.handleKey = this.handleKey.bind(this);
    if (!this.keyValue) {
      const ariaKeyShortcuts = this.element.getAttribute('aria-keyshortcuts');
      if (ariaKeyShortcuts) {
        this.keyValue = ariaKeyShortcuts;
      }
    }
  }

  handleKey(event: Event) {
    if (event.preventDefault) event.preventDefault();
    this.element.click();
  }

  /**
   * When a key is set or changed, bind the handler to the keyboard shortcut.
   * This will override the shortcut, if already set.
   */
  keyValueChanged(key: string, previousKey: string) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey);
    }

    Mousetrap.bind(key, this.handleKey);
  }
}
