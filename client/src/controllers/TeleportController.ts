import { Controller } from '@hotwired/stimulus';
import { runInlineScripts } from '../utils/runInlineScripts';

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
    reset: { default: false, type: Boolean },
    target: { default: '', type: String },
  };

  /** If true, keep the original DOM element intact, otherwise remove it when cloned. */
  declare keepValue: boolean;
  /** If true, empty the target element's contents before appending the cloned element. */
  declare resetValue: boolean;
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
      target.append(...this.templateFragment.childNodes);
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

    if (!(target instanceof Element)) {
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
   */
  get templateFragment() {
    const content = this.element.content;
    // https://developer.mozilla.org/en-US/docs/Web/API/Node/cloneNode (returns the same type)
    // https://github.com/microsoft/TypeScript/issues/283 (TypeScript will return as Node, incorrectly)
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
