import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

// import with side-effect to add global-bind plugin (see https://github.com/ccampbell/mousetrap/tree/master/plugins/global-bind)
import 'mousetrap/plugins/global-bind/mousetrap-global-bind';

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
 * @example - use `mod` for `ctrl` on Windows and `cmd` on MacOS
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key="mod+s">Trigger me with <kbd>ctrl+p</kbd> on Windows or <kbd>cmd+p</kbd> on MacOS.</button>
 * ```
 *
 * @example - use 'global' scope to allow the shortcut to work even when an input is focused
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key="mod+s" data-w-kbd-scope-value="global">Trigger me globally.</button>
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
  static values = {
    key: { default: '', type: String },
    scope: { default: '', type: String },
  };

  /** Keyboard shortcut string. */
  declare keyValue: string;
  /** Scope of the keyboard shortcut, defaults to the normal MouseTrap (non-input) scope. */
  declare scopeValue: '' | 'global';

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

    if (this.scopeValue === 'global') {
      Mousetrap.bindGlobal(key, this.handleKey);
    } else {
      Mousetrap.bind(key, this.handleKey);
    }
  }
}
