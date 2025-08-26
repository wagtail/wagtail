import { Controller } from '@hotwired/stimulus';
import Mousetrap from 'mousetrap';

// import with side-effect to add global-bind plugin (see https://github.com/ccampbell/mousetrap/tree/master/plugins/global-bind)
import 'mousetrap/plugins/global-bind/mousetrap-global-bind';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { forceFocus } from '../utils/forceFocus';

export enum KeyboardAction {
  CLICK = 'click',
  FOCUS = 'focus',
}

/**
 * Adds the ability to trigger a button click event using a
 * keyboard shortcut declared on the controlled element.
 *
 * @see https://craig.is/killing/mice
 *
 * @example
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key-value="[">Trigger me with the <kbd>[</kbd> key.</button>
 * ```
 *
 * @example - use 'mod' for 'ctrl' on Windows and 'cmd' on MacOS
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key-value="mod+s">Trigger me with <kbd>ctrl+p</kbd> on Windows or <kbd>cmd+p</kbd> on MacOS.</button>
 * ```
 *
 * @example - use 'global' scope to allow the shortcut to work even when an input is focused
 * ```html
 * <button type="button" data-controller="w-kbd" data-w-kbd-key-value="mod+s" data-w-kbd-scope-value="global">Trigger me globally.</button>
 * ```
 *
 * @example - use aria-keyshortcuts (when the key string is compatible with Mousetrap's syntax)
 * @see https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes/aria-keyshortcuts
 * ```html
 * <button type="button" data-controller="w-kbd" aria-keyshortcuts="alt+p">Trigger me with alt+p.</button>
 * ```
 *
 * @example - use a target element to trigger the click on a different element
 * ```html
 * <section type="button" data-controller="w-kbd" data-w-kbd-key-value="[">
 *   Trigger my button with the <kbd>[</kbd> key.
 *   <button type="button" id="my-button" data-w-kbd-target="element">My Button</button>
 * </section>
 * ```
 *
 * @example - trigger a focus instead of a click
 * ```html
 * <input type="text" data-controller="w-kbd" data-w-kbd-action-value="focus" data-w-kbd-key-value="x">
 *   Focus on this input with the <kbd>x</kbd> key.
 * </input>
 * ```
 */
export class KeyboardController extends Controller<
  HTMLButtonElement | HTMLAnchorElement
> {
  static targets = ['element'];

  static values = {
    action: { default: '', type: String },
    key: { default: '', type: String },
    scope: { default: '', type: String },
  };

  /** The action to perform when the keyboard shortcut is triggered, uses `"click"` if not defined. */
  declare actionValue: KeyboardAction;
  /** Keyboard shortcut string. */
  declare keyValue: string;
  /** Scope of the keyboard shortcut, defaults to the normal MouseTrap (non-input) scope. */
  declare scopeValue: '' | 'global';

  /** Allow an explicit target to be the element that the keyboard activates instead of the controlled element. */
  declare readonly elementTargets: HTMLElement[];

  /**
   * If custom keyboard shortcuts are disabled by user in settings then controller will not be loaded.
   */
  static get shouldLoad() {
    return !!WAGTAIL_CONFIG.KEYBOARD_SHORTCUTS_ENABLED;
  }

  /**
   * Set up the handleKey binding and check for an aria-keyshortcuts attribute to
   * use as a fallback if the key value is not set.
   */
  initialize() {
    this.handleKey = this.handleKey.bind(this);

    if (!this.keyValue) {
      const ariaKeyShortcuts = [...this.elementTargets, this.element]
        .find((element) => element.hasAttribute('aria-keyshortcuts'))
        ?.getAttribute('aria-keyshortcuts');

      if (ariaKeyShortcuts) {
        this.keyValue = ariaKeyShortcuts;
      }
    }
  }

  /**
   * Handle the key event by preventing the default action and performing the specified action.
   */
  handleKey(event: Event) {
    if (event.preventDefault) event.preventDefault();
    const targetElement =
      this.elementTargets.length > 0 ? this.elementTargets[0] : this.element;
    if (this.actionValue === KeyboardAction.FOCUS) {
      this.handleFocus(targetElement);
    } else {
      this.handleClick(targetElement);
    }
  }

  /**
   * Handle the click action on target element.
   */
  handleClick(target: HTMLElement) {
    target.click();
  }

  /**
   * Handle the focus action on target element. If it is an input element containing text,
   * also selects the existing text inside the field.
   */
  handleFocus(target: HTMLElement) {
    forceFocus(target);

    if (target instanceof HTMLInputElement && target.value && target.select) {
      target.select();
    }
  }

  /**
   * When a key is set or changed, bind the handler to the keyboard shortcut.
   * This will override the shortcut, if already set.
   * Allow key to be empty, so it can be removed from the attributes to unbind the shortcuts
   */
  keyValueChanged(key: string, previousKey: string) {
    if (previousKey && previousKey !== key) {
      Mousetrap.unbind(previousKey);
    }

    if (!key) return;

    if (this.scopeValue === 'global') {
      Mousetrap.bindGlobal(key, this.handleKey);
    } else {
      Mousetrap.bind(key, this.handleKey);
    }
  }
}
