import { Controller } from '@hotwired/stimulus';

export class DrilldownController extends Controller<HTMLElement> {
  static targets = ['menu', 'toggle'];

  static values = {
    activeSubmenu: { default: '', type: String },
  };

  declare activeSubmenuValue: string;
  declare swapSuccessListener: (e: Event) => void;

  declare readonly menuTarget: HTMLElement;
  declare readonly toggleTargets: HTMLButtonElement[];

  connect() {
    this.updateToggleCounts();

    this.swapSuccessListener = (e: Event) => {
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
        const queryString = '?' + filteredParams.toString();
        this.updateToggleCounts();
        window.history.replaceState(null, '', queryString);
      }
    };

    document.addEventListener('w-swap:success', this.swapSuccessListener);
  }

  disconnect() {
    document.removeEventListener('w-swap:success', this.swapSuccessListener);
  }

  open(e: MouseEvent) {
    const toggle = (e.target as HTMLElement)?.closest(
      'button',
    ) as HTMLButtonElement;
    this.activeSubmenuValue = toggle.getAttribute('aria-controls') || '';
  }

  close() {
    this.activeSubmenuValue = '';
    this.updateToggleCounts();
  }

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
    this.element.classList.toggle('w-drilldown--active', expanded);

    if (expanded) {
      content.focus();
    } else {
      toggle.focus();
    }
  }

  /**
   * Placeholder function until this is more correctly set up with the backend.
   */
  updateToggleCounts() {
    let sum = 0;

    this.toggleTargets.forEach((toggle) => {
      const content = this.element.querySelector<HTMLElement>(
        `#${toggle.getAttribute('aria-controls')}`,
      );
      const counter = toggle.querySelector<HTMLElement>('.w-drilldown__count');
      if (!content || !counter) {
        return;
      }
      // Hack to detect fields with a non-default value.
      const nbActiveFields = content.querySelectorAll(
        '[type="checkbox"]:checked, [type="radio"]:checked:not([id$="_0"]), option:checked:not(:first-child), input:not([type="checkbox"], [type="radio"]):not(:placeholder-shown)',
      ).length;
      counter.hidden = nbActiveFields === 0;
      counter.textContent = nbActiveFields.toString();
      sum += nbActiveFields;
    });

    const sumCounter = this.element.querySelector<HTMLElement>(
      '.w-drilldown__count',
    );
    if (!sumCounter) {
      return;
    }
    sumCounter.hidden = sum === 0;
    sumCounter.textContent = sum.toString();
  }
}
