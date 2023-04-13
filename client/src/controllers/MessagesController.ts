
import { Controller } from '@hotwired/stimulus';

declare global {
  interface Window {
    handleUnsavedEvent: (event: CustomEvent<{
      formDirty: boolean;
      commentsDirty: boolean;
    }>) => void;
  }
}
export default class extends Controller {
  static targets = ["container", "template"];
  static values = { clearDelay: Number ,clearDelayValue: Number};

  declare readonly addedClass: string;
  declare readonly containerTarget: HTMLElement;
  declare readonly hasAddedClass: boolean;
  declare readonly hasContainerTarget: boolean;
  declare readonly hasShowClass: boolean;
  declare readonly showClass: string;
  declare readonly templateTarget: HTMLTemplateElement;
  declare readonly templateTargets: HTMLTemplateElement[];

  declare showDelayValue: number;
  declare element: HTMLElement;
  declare clearDelayValue: number;

  static afterLoad() {
    window.handleUnsavedEvent = (event) => {
      const { formDirty, commentsDirty } = event.detail;
      const anyDirty = formDirty || commentsDirty;
      const allDirty = formDirty && commentsDirty;
      const type = allDirty ? "all" : commentsDirty ? "comments" : "edits";
      const detail = { type };
      const eventName = anyDirty ? "w-unsaved:show" : "w-unsaved:hide";
      document.dispatchEvent(new CustomEvent(eventName, { detail }));
    };
  }

add(
  event?: CustomEvent<{
    /** Flag for clearing or stacking messages */
    clear?: boolean;
    /** Content for the message, HTML not supported. */
    text?: string;
    /** Message status level, based on Django's message types. */
    type?: 'success' | 'error' | 'warning' | string;
  }>
) {
  const { clear = false, text = '', type } = event?.detail || {};

  if (this.hasAddedClass) {
    this.element!.classList.add(this.addedClass);
  }

  if (clear) {
    setTimeout(() => {
      this.clear().then(() => {
        this.add(event);
      });
    }, this.clearDelayValue);
    return;
  }

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
    return new Promise((resolve) => {
      this.containerTarget.classList.remove("footer__container--visible");
      setTimeout(() => {
        this.containerTarget.innerHTML = "";
        this.containerTarget.hidden = true;
        resolve(undefined);
      }, this.clearDelayValue);
    });
  }

  show() {
    this.containerTarget.hidden = false;
    this.containerTarget.classList.add("footer__container--visible");
  }

  hide() {
    this.containerTarget.classList.remove("footer__container--visible");
    this.containerTarget.hidden = true;
  }

  dispatch(eventName: string, detail: any = {}) {
    const customEvent = new CustomEvent(eventName, {
      bubbles: true,
      detail,
    });

    this.element.dispatchEvent(customEvent);
  }}