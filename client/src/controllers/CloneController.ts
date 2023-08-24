import { Controller } from '@hotwired/stimulus';

/**
 * Adds the ability for a controlled element to pick an element from a template
 * and then clone that element, adding it to the container.
 * Additionally, it will allow for clearing all previously added elements.
 *
 * @example - Using with the w-messages identifier
 * <div
 *   data-controller="w-messages"
 *   data-action="w-messages:add@document->w-messages#add"
 *   data-w-messages-added-class="new"
 *   data-w-messages-show-class="appear"
 * >
 *   <ul data-w-messages-target="container"></ul>
 *   <template data-w-messages-target="template">
 *     <li data-message-status="error-or-success"><span></span></li>
 *  </template>
 * </div>
 */
export class CloneController extends Controller<HTMLElement> {
  static classes = ['added', 'show'];
  static targets = ['container', 'template'];
  static values = {
    showDelay: { default: 100, type: Number },
  };

  declare readonly addedClass: string;
  declare readonly containerTarget: HTMLElement;
  declare readonly hasAddedClass: boolean;
  declare readonly hasContainerTarget: boolean;
  declare readonly hasShowClass: boolean;
  declare readonly showClass: string;
  declare readonly templateTarget: HTMLTemplateElement;
  declare readonly templateTargets: HTMLTemplateElement[];

  declare showDelayValue: number;

  add(
    event?: CustomEvent<{
      /** Flag for clearing or stacking messages */
      clear?: boolean;
      /** Content for the message, HTML not supported. */
      text?: string;
      /** Message status level, based on Django's message types. */
      type?: 'success' | 'error' | 'warning' | string;
    }>,
  ) {
    const { clear = false, text = '', type } = event?.detail || {};

    if (this.hasAddedClass) {
      this.element.classList.add(this.addedClass);
    }

    if (clear) this.clear();

    /** if no type provided, return the first template target, otherwise try to find
     * a matching target, finally fall back on the first template target if nothing
     * is found.
     */
    const template =
      (type &&
        this.templateTargets.find(({ dataset }) => dataset.type === type)) ||
      this.templateTarget;

    const content = template.content.firstElementChild?.cloneNode(true);

    if (content instanceof HTMLElement) {
      const textElement = content.lastElementChild;

      if (textElement instanceof HTMLElement && text) {
        textElement.textContent = text;
      }

      this.containerTarget.appendChild(content);

      this.dispatch('added');

      if (this.hasShowClass) {
        setTimeout(() => {
          this.element.classList.add(this.showClass);
        }, this.showDelayValue);
      }
    }
  }

  clear() {
    this.containerTarget.innerHTML = '';
  }
}
