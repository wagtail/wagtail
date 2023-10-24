import { Controller } from '@hotwired/stimulus';

type ToggleAllOptions = {
  /** Override check all behaviour to either force check or uncheck all */
  force?: boolean;
};

/**
 * Adds the ability to collectively toggle a set of (non-disabled) checkboxes.
 *
 * @example - Basic usage
 * <div data-controller="w-bulk">
 *   <input type="checkbox" data-action="w-bulk#toggleAll" data-w-bulk-target="all">
 *   <div>
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item" disabled>
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item">
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item">
 *   </div>
 *   <button data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
 *   <button data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
 * </div>
 *
 * @example - Showing and hiding an actions container
 * <div data-controller="w-bulk" data-w-bulk-action-inactive-class="w-invisible">
 *   <div class="w-invisible" data-w-bulk-target="action" id="inner-actions">
 *     <button type="button">Some action</button>
 *   </div>
 *   <input data-action="w-bulk#toggleAll" data-w-bulk-target="all" type="checkbox"/>
 *   <div id="checkboxes">
 *     <input data-action="w-bulk#toggle" data-w-bulk-target="item" disabled="" type="checkbox" />
 *     <input data-action="w-bulk#toggle" data-w-bulk-target="item" type="checkbox"/>
 *     <input data-action="w-bulk#toggle" data-w-bulk-target="item" type="checkbox" />
 *   </div>
 * </div>
 *
 */
export class BulkController extends Controller<HTMLElement> {
  static classes = ['actionInactive'];
  static targets = ['action', 'all', 'item'];

  /** Target(s) that will have the `actionInactive` classes removed if any actions are checked */
  declare readonly actionTargets: HTMLElement[];

  /** All select-all checkbox targets */
  declare readonly allTargets: HTMLInputElement[];

  /** All item checkbox targets */
  declare readonly itemTargets: HTMLInputElement[];

  /** Classes to remove on the actions target if any actions are checked */
  declare readonly actionInactiveClasses: string[];

  /** Internal tracking of last clicked for shift+click behaviour */
  lastChanged?: HTMLElement | null;

  /** Internal tracking of whether the shift key is active for multiple selection */
  shiftActive?: boolean;

  /**
   * On creation, ensure that the select all checkboxes are in sync.
   * Set up the event listeners for shift+click behaviour.
   */
  connect() {
    this.toggle();
    this.handleShiftKey = this.handleShiftKey.bind(this);
    document.addEventListener('keydown', this.handleShiftKey);
    document.addEventListener('keyup', this.handleShiftKey);
  }

  /**
   * Returns all valid targets (i.e. not disabled).
   */
  getValidTargets(
    targets: HTMLInputElement[] = this.itemTargets,
  ): HTMLInputElement[] {
    return targets.filter(({ disabled }) => !disabled);
  }

  /**
   * Event handler to determine if shift key is pressed.
   */
  handleShiftKey(event: KeyboardEvent) {
    if (!event) return;

    const { shiftKey, type } = event;

    if (type === 'keydown' && shiftKey) {
      this.shiftActive = true;
    }

    if (type === 'keyup' && this.shiftActive) {
      this.shiftActive = false;
    }
  }

  /**
   * When an item is toggled, ensure the select all targets are kept in sync.
   * Update the classes on the action targets to reflect the current state.
   * If the shift key is pressed, toggle all the items between the last clicked
   * item and the current item.
   */
  toggle(event?: Event) {
    const activeItems = this.getValidTargets();
    const lastChanged = this.lastChanged;

    if (this.shiftActive && lastChanged instanceof HTMLElement) {
      this.shiftActive = false;

      const lastClickedIndex = activeItems.findIndex(
        (item) => item === lastChanged,
      );
      const currentIndex = activeItems.findIndex(
        (item) => item === event?.target,
      );

      const [start, end] = [lastClickedIndex, currentIndex].sort(
        // eslint-disable-next-line id-length
        (a, b) => a - b,
      );

      activeItems.forEach((target, index) => {
        if (index >= start && index <= end) {
          // eslint-disable-next-line no-param-reassign
          target.checked = !!activeItems[lastClickedIndex].checked;
          this.dispatch('change', { target, bubbles: true });
        }
      });
    }

    this.lastChanged =
      activeItems.find((item) => item.contains(event?.target as Node)) ?? null;

    const totalCheckedItems = activeItems.filter((item) => item.checked).length;
    const isAnyChecked = totalCheckedItems > 0;
    const isAllChecked = totalCheckedItems === activeItems.length;

    this.getValidTargets(this.allTargets).forEach((target) => {
      // eslint-disable-next-line no-param-reassign
      target.checked = isAllChecked;
    });

    const actionInactiveClasses = this.actionInactiveClasses;
    if (!actionInactiveClasses.length) return;

    this.actionTargets.forEach((element) => {
      actionInactiveClasses.forEach((actionInactiveClass) => {
        element.classList.toggle(actionInactiveClass, !isAnyChecked);
      });
    });
  }

  /**
   * Toggles all item checkboxes, can be used to force check or uncheck all.
   * If the event used to trigger this method does not have a suitable target,
   * the first allTarget will be used to determine the current checked value.
   */
  toggleAll(
    event: CustomEvent<ToggleAllOptions> & { params?: ToggleAllOptions },
  ) {
    const { force = null } = {
      ...event.detail,
      ...event.params,
    };

    this.lastChanged = null;

    let isChecked = false;

    if (typeof force === 'boolean') {
      isChecked = force;
    } else if (event.target instanceof HTMLInputElement) {
      isChecked = event.target.checked;
    } else {
      const checkbox = this.allTargets[0];
      // use the opposite of the current state
      // as this is being triggered by an external call
      isChecked = !checkbox?.checked;
    }

    this.getValidTargets().forEach((target) => {
      if (target.checked !== isChecked) {
        // eslint-disable-next-line no-param-reassign
        target.checked = isChecked;
        target.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    this.toggle();
  }

  disconnect() {
    document?.removeEventListener('keydown', this.handleShiftKey);
    document?.removeEventListener('keyup', this.handleShiftKey);
  }
}
