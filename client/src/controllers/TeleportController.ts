import { Controller } from '@hotwired/stimulus';

/**
 * Allows the controlled element's content to be copied and appended
 * to another place in the DOM. Once copied, the original controlled
 * element will be removed from the DOM unless `keep` is true.
 * If a target selector isn't provided, a default target of
 * `document.body` or the Shadow Root's first DOM node will be used.
 * Depending on location of the controlled element.
 *
 * @example
 * <aside>
 *   <template
 *    data-controller="w-teleport"
 *    data-w-teleport-target-value="#other-location"
 *   >
 *    <div class="content-to-clone">Some content</div>
 *   </template>
 *   <div id="other-location"></div>
 * </aside>
 */
export class TeleportController extends Controller<HTMLTemplateElement> {
  static values = {
    keep: { default: false, type: Boolean },
    target: { default: '', type: String },
  };

  /** If true, keep the original DOM element intact, otherwise remove it when cloned. */
  declare keepValue: boolean;
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
      target.append(this.templateElement);
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

    if (this.targetValue) {
      target = document.querySelector(this.targetValue);
    } else {
      const rootNode = this.element.getRootNode();
      target =
        rootNode instanceof Document ? rootNode.body : rootNode.firstChild;
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
   * Resolve a valid HTMLElement from the controlled element's children.
   */
  get templateElement() {
    const templateElement =
      this.element.content.firstElementChild?.cloneNode(true);

    if (!(templateElement instanceof HTMLElement)) {
      throw new Error('Invalid template content.');
    }

    return templateElement;
  }
}
