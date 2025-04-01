import { Controller } from '@hotwired/stimulus';

import { forceFocus } from '../utils/forceFocus';

/**
 * Allows a target element (either via `href` or the targetValue as a selector) to be focused.
 * If the element does not have a `tabindex` attribute, it will be added and removed when the element loses focus.
 *
 * @description
 * Useful for the skip link functionality, which appears at the top left corner of the admin when the tab button is clicked.
 * Used to provide an accessible skip button for keyboard control so that users can
 * easily navigate to the main content without having to navigate a long list of navigation links.
 * Inspired by https://github.com/selfthinker/dokuwiki_template_writr/blob/master/js/skip-link-focus-fix.js
 *
 * @example As an accessible skip link
 * ```html
 * <a href="#main" data-controller="w-focus" data-action="w-focus#focus:prevent">Skip to main content</a>
 * ```
 *
 * @example As a button to skip to the top of a section
 * ```html
 * <section>
 *   <div class="section-top"><h3>Section title</h3></div>
 *   <p>...lots of content...</p>
 *   <button type="button" data-controller="w-focus" data-w-focus-target-value=".section-top" data-action="w-focus#focus">Skip to top</button>
 * </section>
 * ```
 */
export class FocusController extends Controller<
  HTMLAnchorElement | HTMLButtonElement
> {
  static values = {
    target: String,
  };

  declare targetValue: string;

  get target() {
    const selector =
      this.targetValue || this.element.getAttribute('href') || 'main';

    return (
      this.element.closest<HTMLElement>(selector) ||
      document.querySelector<HTMLElement>(selector)
    );
  }

  focus() {
    const target = this.target;

    if (target) {
      forceFocus(target);
      this.dispatch('focused', { bubbles: true, cancelable: false, target });
    }
  }
}
