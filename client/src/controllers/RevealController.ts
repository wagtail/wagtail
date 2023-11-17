import { Controller } from '@hotwired/stimulus';

/**
 * Adds the ability to make the controlled element be used as an
 * opening/closing (aka collapsing) element.
 * Supports, and relies on, correct usage of aria-* attributes.
 *
 * @see https://w3c.github.io/aria/#aria-expanded
 *
 * @example
 * <section data-controller="w-reveal">
 *  <button type="button" data-action="w-reveal#toggle" data-w-reveal-target="toggle" aria-controls="my-content" type="button">Toggle</button>
 *  <div id="my-content">CONTENT</div>
 * </section>
 */
export class RevealController extends Controller<HTMLElement> {
  static classes = [
    'closed',
    'closeIcon',
    'opened',
    'openedContent',
    'openIcon',
  ];

  static targets = ['content', 'toggle'];

  static values = {
    closed: { default: false, type: Boolean },
    peeking: { default: false, type: Boolean },
    peekTarget: { default: '', type: String },
  };

  declare closedValue: boolean;
  declare peekingValue: boolean;

  declare readonly closedClass: string;
  declare readonly closedClasses: string[];
  declare readonly closeIconClass: string;
  declare readonly contentTarget: HTMLElement;
  declare readonly contentTargets: HTMLElement[];
  declare readonly hasClosedClass: boolean;
  declare readonly hasCloseIconClass: string;
  declare readonly hasContentTarget: boolean;
  declare readonly hasOpenIconClass: string;
  declare readonly hasToggleTarget: boolean;
  declare readonly initialClasses: string[];
  declare readonly openedClasses: string[];
  declare readonly openedContentClasses: string[];
  declare readonly openIconClass: string;
  declare readonly peekTargetValue: string;
  declare readonly toggleTarget: HTMLButtonElement;
  declare readonly toggleTargets: HTMLButtonElement[];

  cleanUpPeekListener?: () => void;

  connect() {
    // If peeking is being used, set up listener and its removal on disconnect

    const peekZone = this.peekTargetValue
      ? this.element.closest<HTMLElement>(this.peekTargetValue)
      : false;

    if (peekZone) {
      const onMouseLeave = () => {
        if (this.peekingValue) this.close();
        this.peekingValue = false;
      };
      peekZone.addEventListener('mouseleave', onMouseLeave, { passive: true });
      this.cleanUpPeekListener = () => {
        peekZone.removeEventListener('mouseleave', onMouseLeave);
      };
    }

    // Dispatch initial event & class removal after timeout (allowing other JS content to load)

    new Promise((resolve) => {
      setTimeout(resolve);
    }).then(() => {
      this.dispatch('ready', {
        cancelable: false,
        detail: {
          closed: this.closedValue,
        },
      });
    });
  }

  closedValueChanged(shouldClose: boolean, previouslyClosed?: boolean) {
    if (previouslyClosed === shouldClose) return;

    const closedClasses = this.closedClasses;
    const openedClasses = this.openedClasses;
    const contentTargets = this.contentTargets;
    const isInitial = previouslyClosed === undefined;
    const isPeeking = this.peekingValue;
    const openedContentClasses = this.openedContentClasses;
    const toggles = this.toggles;

    if (!isPeeking) this.updateToggleIcon(shouldClose);

    if (shouldClose) {
      const event = this.dispatch('closing', { cancelable: true });
      if (event.defaultPrevented) return;
      toggles.forEach((toggle) => {
        toggle.setAttribute('aria-expanded', 'false');
      });
      contentTargets.forEach((content) => {
        content.classList.remove(...openedContentClasses);
        // eslint-disable-next-line no-param-reassign
        content.hidden = true;
      });
      this.element.classList.add(...closedClasses);
      this.element.classList.remove(...openedClasses);
      this.dispatch('closed', { cancelable: false });
    } else {
      const event = this.dispatch('opening', { cancelable: true });
      if (event.defaultPrevented) return;
      toggles.forEach((toggle) => {
        toggle.setAttribute('aria-expanded', 'true');
      });
      contentTargets.forEach((content) => {
        content.classList.add(...openedContentClasses);
        content.hidden = false; // eslint-disable-line no-param-reassign
      });
      this.element.classList.remove(...closedClasses);
      this.element.classList.add(...openedClasses);
      this.dispatch('opened', { cancelable: false });
    }

    if (isInitial) return;
    // If we have known toggles, dispatch on those buttons
    toggles.forEach((target) => {
      this.dispatch('toggled', {
        cancelable: false,
        detail: {
          closed: shouldClose,
        },
        target,
      });
    });
  }

  close() {
    this.closedValue = true;
  }

  open() {
    this.closedValue = false;
  }

  peek() {
    if (this.closedValue) {
      this.peekingValue = true;
      this.open();
    }
  }

  toggle() {
    if (this.peekingValue) {
      this.peekingValue = false;
      // if peeking and toggle clicked, is already open
      // visually set the icon to the opened variant so it can be closed.
      this.updateToggleIcon(false);
      return;
    }
    this.closedValue = !this.closedValue;
  }

  /**
   * Collects all toggles, those controlled by this controller and any external
   * that have an aria-controls references to any content target elements.
   */
  get toggles() {
    const toggles = this.contentTargets
      .map((content) => content.id)
      .flatMap((id) =>
        Array.from(
          document.querySelectorAll<HTMLButtonElement>(
            `[aria-controls~="${id}"]`,
          ),
        ),
      )
      .concat(...this.toggleTargets);
    return Array.from(new Set(toggles));
  }

  /**
   * Set the inner icon on any toggles (in scope or out of scope).
   */
  updateToggleIcon(isOpenIcon = false) {
    if (!this.hasCloseIconClass || !this.hasOpenIconClass) return;
    const closeIconClass = this.closeIconClass;
    const openIconClass = this.openIconClass;
    if (closeIconClass === openIconClass) return;

    this.toggles
      .map((toggle) => {
        const iconElement = toggle.querySelector<HTMLSpanElement>('.icon');
        const useElement = iconElement?.querySelector<SVGUseElement>('use');
        if (!useElement || !iconElement) return [];
        return [iconElement, useElement] as const;
      })
      .filter(({ length }) => length)
      .forEach(([iconElement, useElement]) => {
        if (isOpenIcon) {
          iconElement.classList.remove(closeIconClass);
          iconElement.classList.add(openIconClass);
          useElement.setAttribute('href', `#${openIconClass}`);
        } else {
          iconElement.classList.remove(openIconClass);
          iconElement.classList.add(closeIconClass);
          useElement.setAttribute('href', `#${closeIconClass}`);
        }
      });
  }

  disconnect() {
    this.cleanUpPeekListener?.call(this);
  }
}
