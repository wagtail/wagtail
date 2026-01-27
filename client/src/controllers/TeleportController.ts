import { Controller } from '@hotwired/stimulus';
import { runInlineScripts } from '../utils/runInlineScripts';

/**
 * Modes for teleporting content.
 *
 * - `innerHTML`: Replace the `.innerHTML` of the target element
 * - `outerHTML`: Replace the `.outerHTML` of the target element
 * - `textContent`: Replace the `.textContent` of the target element, without parsing the template content as HTML
 * - `beforebegin`: Insert the template content before the target element
 * - `afterbegin`: Insert the template content before the first child of the target element
 * - `beforeend`: Insert the template content after the last child of the target element
 * - `afterend`: Insert the template content after the target element
 */
export enum TeleportMode {
  innerHTML = 'innerHTML',
  outerHTML = 'outerHTML',
  textContent = 'textContent',
  beforebegin = 'beforebegin',
  afterbegin = 'afterbegin',
  beforeend = 'beforeend',
  afterend = 'afterend',
}

/**
 * Allows the controlled element's content to be copied and appended
 * to another place in the DOM. Once copied, the original controlled
 * element will be removed from the DOM unless `keep` is true.
 * If `reset` is true, the target element will be emptied before
 * the controlled element is appended.
 * If a target selector isn't provided, a default target of
 * `document.body` or the Shadow Root's first DOM node will be used.
 * Depending on location of the controlled element.
 *
 * @example
 * ```html
 * <aside>
 *   <template
 *     data-controller="w-teleport"
 *     data-w-teleport-target-value="#other-location"
 *   >
 *     <div class="content-to-clone">Some content</div>
 *   </template>
 *   <div id="other-location"></div>
 * </aside>
 * ```
 */
export class TeleportController extends Controller<HTMLTemplateElement> {
  static values = {
    keep: { default: false, type: Boolean },
    mode: { default: TeleportMode.beforeend, type: String },
    reset: { default: false, type: Boolean },
    target: { default: '', type: String },
  };

  /** If true, keep the original DOM element intact, otherwise remove it when cloned. */
  declare keepValue: boolean;
  /**
   * If true, empty the target element's contents before appending the cloned element.
   * @deprecated RemovedInWagtail80Warning Use `modeValue` with `innerHTML` or `outerHTML` instead.
   */
  declare resetValue: boolean;
  /**
   * The mode to use when inserting the cloned element into the target.
   * @see TeleportMode for available modes.
   * Defaults to `beforeend` to preserve legacy behavior.
   */
  declare modeValue: TeleportMode;
  /** A selector to determine the target location to clone the element. */
  declare targetValue: string;

  connect() {
    this.append();
  }

  append() {
    const target = this.target;
    let completed = false;

    const complete = () => {
      if (completed) return;
      if (this.resetValue) target.innerHTML = '';

      // Using string-based operations like innerHTML, outerHTML, or
      // insertAdjacentHTML will not run scripts. And we cannot rely on the
      // runInlineScripts utility here as it requires the elements to already be
      // in the DOM. Even then, without additional tracking we would not be able
      // to select the exact scripts that were in the template when using
      // outerHTML, beforebegin, or afterend modes.

      // So, we move the cloned DocumentFragment from the template into the DOM
      // using node-based operations instead. This would execute any scripts in
      // the template, and allows the template to contain any type of content
      // (including text nodes).
      switch (this.modeValue) {
        case TeleportMode.outerHTML:
          target.replaceWith(this.templateFragment);
          break;
        case TeleportMode.innerHTML:
          target.innerHTML = '';
          target.append(this.templateFragment);
          break;
        case TeleportMode.textContent:
          target.textContent = this.templateFragment.textContent;
          break;
        case TeleportMode.beforebegin:
          target.parentElement?.insertBefore(this.templateFragment, target);
          break;
        case TeleportMode.afterbegin:
          target.prepend(this.templateFragment);
          break;
        case TeleportMode.beforeend:
          target.append(this.templateFragment);
          break;
        case TeleportMode.afterend:
          target.parentElement?.insertBefore(
            this.templateFragment,
            target.nextSibling,
          );
          break;
        default:
          target.append(this.templateFragment);
          break;
      }

      this.dispatch('appended', { cancelable: false, detail: { target } });
      completed = true;
      if (this.keepValue) return;
      this.element.remove();
    };

    const event = this.dispatch('append', {
      cancelable: true,
      detail: { complete, target },
    });

    if (!event.defaultPrevented) complete();
  }

  /**
   * Resolve a valid target element, defaulting to the document.body
   * or the shadow root's first DOM node if no target selector provided.
   */
  get target() {
    let target: any;
    const root = this.element.getRootNode() as Document | ShadowRoot;

    if (this.targetValue) {
      // Look for the target in the shadow root first, then the document, as
      // using document.querySelector won't match elements in the shadow root.
      target =
        root.querySelector(this.targetValue) ||
        document.querySelector(this.targetValue);
    } else {
      // If no target selector is provided, default to the body if the root node
      // is a document, otherwise use the first element in the shadow root.
      target = root instanceof Document ? root.body : root.firstElementChild;
    }

    if (!(target instanceof HTMLElement)) {
      throw new Error(
        `No valid target container found at ${
          this.targetValue ? `'${this.targetValue}'` : 'the root node'
        }.`,
      );
    }

    return target;
  }

  /**
   * Returns a fresh copy of the DocumentFragment from the controlled element.
   *
   * @see https://developer.mozilla.org/en-US/docs/Web/API/Node/cloneNode (returns the same type)
   * @see https://github.com/microsoft/TypeScript/issues/283 (TypeScript will return as Node, incorrectly)
   */
  get templateFragment() {
    const content = this.element.content;
    const templateFragment = content.cloneNode(true) as typeof content;

    // HACK:
    // cloneNode doesn't run scripts, so we need to create new script elements
    // and copy the attributes and innerHTML over. This is necessary when we're
    // teleporting a template that contains legacy init code, e.g. initDateChooser.
    // Only do this for inline scripts, as that's what we're expecting.
    runInlineScripts(templateFragment);

    return templateFragment;
  }
}
