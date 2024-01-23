import { Controller } from '@hotwired/stimulus';

/**
 * Drilldown menu interaction combined with URL-driven
 * state management for listing filters.
 */
export class DrilldownController extends Controller<HTMLElement> {
  static targets = ['count', 'menu', 'toggle'];

  static values = {
    // Default: main menu.
    activeSubmenu: { default: '', type: String },
    countAttr: { default: '', type: String },
  };

  declare activeSubmenuValue: string;
  declare countAttrValue: string;

  declare readonly countTargets: HTMLElement[];
  declare readonly menuTarget: HTMLElement;
  declare readonly toggleTargets: HTMLButtonElement[];

  countTargetConnected() {
    this.updateCount();
  }

  /**
   * Update the count of items in the menu.
   * This is done by counting the number of elements with the data attribute
   * specified by the countAttrValue value that have the same value as the
   * data-count-name attribute of the countTarget.
   * If the countTarget does not have a data-count-name attribute, then all
   * elements with the data attribute specified by the countAttrValue value
   * are counted.
   */
  updateCount() {
    const total = document.querySelectorAll(`[${this.countAttrValue}]`).length;
    this.countTargets.forEach((countTarget) => {
      const name = countTarget.dataset.countName;
      const count = name
        ? document.querySelectorAll(`[${this.countAttrValue}=${name}]`).length
        : total;
      // eslint-disable-next-line no-param-reassign
      countTarget.hidden = count === 0;
      // eslint-disable-next-line no-param-reassign
      countTarget.textContent = count.toString();
    });
  }

  updateParams(e: Event) {
    const swapEvent = e as CustomEvent<{ requestUrl: string }>;
    if ((e.target as HTMLElement)?.id === 'listing-results') {
      const params = new URLSearchParams(
        swapEvent.detail?.requestUrl.split('?')[1],
      );
      const filteredParams = new URLSearchParams();
      params.forEach((value, key) => {
        if (value.trim() !== '' && !key.startsWith('_w_')) {
          // Check if the value is not empty after trimming white space
          filteredParams.append(key, value);
        }
      });
      const queryString = `?${filteredParams.toString()}`;
      window.history.replaceState(null, '', queryString);
    }
    this.updateCount();
  }

  open(e: MouseEvent) {
    const toggle = (e.target as HTMLElement)?.closest(
      'button',
    ) as HTMLButtonElement;
    this.activeSubmenuValue = toggle.getAttribute('aria-controls') || '';
  }

  close() {
    this.activeSubmenuValue = '';
  }

  /**
   * Delay closing the submenu to allow the top-level menu to fade out first.
   * Useful for resetting the state when the user clicks outside the menu.
   * This can be used as an action for the w-dropdown:hidden event of the menu,
   * e.g. data-action="w-dropdown:hidden->w-drilldown#delayedClose".
   */
  delayedClose() {
    setTimeout(() => this.close(), 200);
  }

  /**
   * Derive the component’s targets based on the state,
   * so the drilldown state can be controlled externally more easily.
   */
  activeSubmenuValueChanged(activeSubmenu: string, prevActiveSubmenu?: string) {
    if (prevActiveSubmenu) {
      const toggle = document.querySelector(
        `[aria-controls="${prevActiveSubmenu}"]`,
      ) as HTMLButtonElement;
      this.toggle(false, toggle);
    }

    if (activeSubmenu) {
      const toggle = document.querySelector(
        `[aria-controls="${activeSubmenu}"]`,
      ) as HTMLButtonElement;
      this.toggle(true, toggle);
    }
  }

  toggle(expanded: boolean, toggle: HTMLButtonElement) {
    const controls = toggle.getAttribute('aria-controls');
    const content = this.element.querySelector<HTMLElement>(`#${controls}`);
    if (!content) {
      return;
    }
    toggle.setAttribute('aria-expanded', expanded.toString());
    content.hidden = !expanded;
    this.menuTarget.hidden = expanded;

    if (expanded) {
      content.focus();
    } else {
      toggle.focus();
    }
  }
}
