/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["hidden","textContent"] }] */

import { Controller } from '@hotwired/stimulus';

import type { ActionController } from './ActionController';
import type { DropdownController } from './DropdownController';

/**
 * Drilldown menu interaction combined with URL-driven
 * state management for listing filters.
 *
 * @example
 * ```html
 * <section>
 *   <div data-controller="w-drilldown" data-w-drilldown-count-attr-value="data-w-active-filter-id">
 *     <div data-w-drilldown-target="menu">
 *       <h2>Filter by</h2>
 *       <button type="button" aria-expanded="false" aria-controls="drilldown-field-0" data-w-drilldown-target="toggle" data-action="click->w-drilldown#open">Field 1</button>
 *       <button type="button" aria-expanded="false" aria-controls="drilldown-field-1" data-w-drilldown-target="toggle" data-action="click->w-drilldown#open">Field 2</button>
 *     </div>
 *     <div id="drilldown-field-0" hidden tabIndex="-1">
 *       <p>...items for field 1</p>
 *       <button type="button" data-action="click->w-drilldown#close">Back</button>
 *     </div>
 *     <div id="drilldown-field-1" hidden tabIndex="-1">
 *       <p>...items for field 2</p>
 *       <button type="button" data-action="click->w-drilldown#close">Back</button>
 *     </div>
 *   </div>
 * </section>
 * ```
 */
export class DrilldownController extends Controller<HTMLElement> {
  static targets = ['count', 'menu', 'toggle'];

  static values = {
    // Default: main menu.
    activeSubmenu: { default: '', type: String },
    countAttr: { default: '', type: String },
  };

  static outlets = [
    // w-action outlet for submenu toggles that are outside the drilldown.
    // We don't really use anything specific to ActionController, we just need
    // a Stimulus controller to be able to use the outlet. As with toggle targets,
    // these need to have aria-controls.
    'w-action',

    // w-dropdown outlet for the popup menu, to allow interacting with the
    // DropdownController programmatically.
    'w-dropdown',
  ];

  /** Currently active submenu id. */
  declare activeSubmenuValue: string;
  /** Attribute used to count items. */
  declare countAttrValue: string;

  /** Targets for displaying item counts. */
  declare readonly countTargets: HTMLElement[];
  /** Main menu target element. */
  declare readonly menuTarget: HTMLElement;
  /** Targets for submenu toggle buttons. */
  declare readonly toggleTargets: HTMLButtonElement[];
  /** Indicates if w-dropdown outlet is present. */
  declare readonly hasWDropdownOutlet: boolean;
  /** Outlets for action controllers. */
  declare readonly wActionOutlets: ActionController[];
  /** Outlet for the dropdown controller. */
  declare readonly wDropdownOutlet: DropdownController;

  countTargetConnected() {
    this.updateCount();
  }

  connect(): void {
    this.open = this.open.bind(this);
  }

  wActionOutletConnected(_: ActionController, element: HTMLElement) {
    element.addEventListener('click', this.open);
  }

  wActionOutletDisconnected(_: ActionController, element: HTMLElement) {
    element.removeEventListener('click', this.open);
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
      countTarget.hidden = count === 0;
      countTarget.textContent = count.toString();
    });
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

  /**
   * Prevent clicks on the w-action outlets from closing the dropdown.
   * Usage: data-action="w-dropdown:clickaway->w-drilldown#preventOutletClickaway"
   */
  preventOutletClickaway(e: Event) {
    const clickawayEvent = e as CustomEvent<{ target: HTMLElement }>;
    const target = clickawayEvent.detail.target;
    if (!target) return;
    const controlledIds = this.toggleTargets.map((toggle) =>
      toggle.getAttribute('aria-controls'),
    );
    const clickawayControl =
      target.closest('button')?.getAttribute('aria-controls') || '';
    if (controlledIds.includes(clickawayControl)) {
      e.preventDefault();
    }
  }

  toggle(expanded: boolean, toggle: HTMLButtonElement) {
    // If we're expanding, the toggle may be inside the w-dropdown outlet while
    // the dropdown is hidden (e.g. opening directly to a submenu from an
    // overall collapsed state).
    // Ensure that the dropdown is shown so Tippy renders the toggle in the DOM.
    if (this.hasWDropdownOutlet && expanded) {
      this.wDropdownOutlet.show();
    }

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
