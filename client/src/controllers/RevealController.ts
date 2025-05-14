/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["hidden"] }] */

import { Controller } from '@hotwired/stimulus';

enum RevealState {
  OPENED = 'opened',
  CLOSED = 'closed',
}

/**
 * Adds the ability to make the controlled element be used as an
 * opening/closing (aka collapsing) element.
 * Supports, and relies on, correct usage of aria-* attributes.
 *
 * @see https://w3c.github.io/aria/#aria-expanded
 *
 * @example - Basic usage
 * ```html
 * <section data-controller="w-reveal">
 *   <button type="button" data-action="w-reveal#toggle" data-w-reveal-target="toggle" aria-controls="my-content" type="button">Toggle</button>
 *   <div id="my-content">CONTENT</div>
 * </section>
 * ```
 *
 * @example - Saving to local storage
 * ```html
 * <section data-controller="w-reveal" data-w-reveal-storage-key="saved-state">
 *   <button type="button" aria-controls="my-content" type="button" data-action="w-reveal#toggle" data-w-reveal-target="toggle">Toggle</button>
 *   <div id="my-content">CONTENT</div>
 * </section>
 * ```
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
    storageKey: { default: '', type: String },
  };

  declare closedValue: boolean;
  declare peekingValue: boolean;

  declare readonly closedClasses: string[];
  declare readonly closeIconClass: string;
  declare readonly hasCloseIconClass: string;
  declare readonly hasOpenIconClass: string;
  declare readonly openedClasses: string[];
  declare readonly openedContentClasses: string[];
  declare readonly openIconClass: string;

  /** Content element target, to be shown/hidden with classes when opened/closed. */
  declare readonly contentTargets: HTMLElement[];
  /** Global selector string to be used to determine the container to add the mouseleave listener to. */
  declare readonly peekTargetValue: string;
  /**  Local storage key to be used to backup the open state of this controller, this can be unique or shared across multiple controllers, it uses the controller identifier for the base.If not provided, the controller will not attempt to store the state to local storage. */
  declare readonly storageKeyValue: string;
  /**  Toggle button element(s) to have their classes and aria attributes updated. */
  declare readonly toggleTargets: HTMLButtonElement[];

  cleanUpPeekListener?: () => void;

  /**
   * Connect the controller, setting up the peeking listener if required,
   * and setting the initial state based on the stored value if available.
   *
   * Finally, dispatch the ready event to signal the controller is ready.
   */
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

    // Set initial state based on stored value if available

    if (this.storageKeyValue) {
      const isStoredAsClosed = this.stored;
      if (
        typeof isStoredAsClosed === 'boolean' &&
        isStoredAsClosed !== this.closedValue
      ) {
        this.closedValue = isStoredAsClosed;
      } else {
        // No value stored yet, so store default(close) state
        this.stored = this.closedValue;
      }
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

  /**
   * Handles changes to the closed state,updating element classes and `aria-expanded` attributes accordingly.
   *
   * Note: This may not trigger when clicking the toggle button if the element is already open in peeking mode.
   */
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
        content.hidden = false;
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

  /**
   * Close (hide) the reveal content.
   */
  close() {
    this.closedValue = true;
  }

  /**
   * Open (show) the reveal content.
   */
  open() {
    this.closedValue = false;
  }

  peek() {
    if (this.closedValue) {
      this.peekingValue = true;
      this.open();
    }
  }

  /**
   * Toggle the open/closed state of the controller, accounting for the peeking state (visually open, but not 'fixed' as open).
   * The updated closed value will be stored in local storage if available.
   */
  toggle() {
    this.stored = this.peekingValue ? false : !this.closedValue;

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

  /**
   * Prepare a unique local storage key for this controller joined with the store value,
   * if not provided then assume we do not want to store the state of this controller.
   */
  get localStorageKey() {
    const storeValue = this.storageKeyValue;
    if (!storeValue) return null;
    return ['wagtail', this.identifier, storeValue].join(':');
  }

  /**
   * Get the stored (closed) state of this controller from local storage.
   * If the key is not available, return undefined.
   */
  get stored(): boolean | undefined {
    const key = this.localStorageKey;
    if (!key) return undefined;
    try {
      const value = localStorage.getItem(key);
      if (value === null) return undefined;
      return value === RevealState.CLOSED;
    } catch (error) {
      //  Ignore if localStorage is not available.
    }
    return undefined;
  }

  /**
   * Set the stored state of this controller in the local storage.
   * If the store key value is not set, do nothing.
   */
  set stored(isClosed: boolean) {
    const key = this.localStorageKey;
    if (!key) return;
    try {
      if (isClosed) {
        localStorage.setItem(key, RevealState.CLOSED);
      } else {
        localStorage.setItem(key, RevealState.OPENED);
      }
    } catch (error) {
      // Ignore if localStorage is not available
    }
  }

  disconnect() {
    this.cleanUpPeekListener?.call(this);
  }
}
