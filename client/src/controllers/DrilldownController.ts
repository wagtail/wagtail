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
  };

  declare activeSubmenuValue: string;

  declare readonly countTarget: HTMLElement;
  declare readonly menuTarget: HTMLElement;
  declare readonly toggleTargets: HTMLButtonElement[];

  connect() {
    const filteredParams = new URLSearchParams(window.location.search);
    this.countTarget.hidden = filteredParams.size === 0;
    this.countTarget.textContent = filteredParams.size.toString();
  }

  updateParamsCount(e: Event) {
    const swapEvent = e as CustomEvent<{ requestUrl: string }>;
    if ((e.target as HTMLElement)?.id === 'listing-results') {
      const params = new URLSearchParams(
        swapEvent.detail?.requestUrl.split('?')[1],
      );
      const filteredParams = new URLSearchParams();
      params.forEach((value, key) => {
        if (value.trim() !== '') {
          // Check if the value is not empty after trimming white space
          filteredParams.append(key, value);
        }
      });
      const queryString = `?${filteredParams.toString()}`;
      window.history.replaceState(null, '', queryString);

      // Update the drilldown’s count badge based on remaining filter parameters.
      this.countTarget.hidden = filteredParams.size === 0;
      this.countTarget.textContent = filteredParams.size.toString();
    }
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
