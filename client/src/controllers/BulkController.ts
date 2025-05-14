/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["checked"] }] */

import { Controller } from '@hotwired/stimulus';

type ToggleOptions = {
  /** Only toggle those within the provided group(s), a space separated set of strings. */
  group?: string;
};

type ToggleAllOptions = ToggleOptions & {
  /** Override check all behavior to either force check or uncheck all */
  force?: boolean;
};

/**
 * Adds the ability to collectively toggle a set of (non-disabled) checkboxes.
 *
 * @example - Basic usage
 * ```html
 * <div data-controller="w-bulk">
 *   <input type="checkbox" data-action="w-bulk#toggleAll" data-w-bulk-target="all">
 *   <div>
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item" disabled>
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item">
 *     <input type="checkbox" data-action="w-bulk#toggle" data-w-bulk-target="item">
 *   </div>
 *   <button type="button" data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
 *   <button type="button" data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
 * </div>
 *
 * @example - Showing and hiding an actions container
 * ```html
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
 * ```
 *
 * @example - Using groups to allow toggles to be controlled separately or together
 * ```html
 * <table data-controller="w-bulk">
 *   <thead>
 *     <tr>
 *       <th>Name</th>
 *       <th>Add</th>
 *       <th>Change</th>
 *     </tr>
 *   </thead>
 *   <tbody>
 *     <tr>
 *       <td>Item 1</td>
 *       <td><input data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add" type="checkbox"/></td>
 *       <td><input data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="change" type="checkbox"/></td>
 *     </tr>
 *     <tr>
 *       <td>Item 2</td>
 *       <td><input data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add" type="checkbox"/></td>
 *       <td><input data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="change" type="checkbox"/></td>
 *     </tr>
 *   </tbody>
 *   <tfoot>
 *     <th scope="row">
 *       Check all (Add & Change)
 *       <input data-action="w-bulk#toggleAll" data-w-bulk-target="all" type="checkbox"/>
 *     </th>
 *     <td>
 *       Check all (Add)
 *       <input data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="add" type="checkbox"/>
 *     </td>
 *     <td>
 *       Check all (Change)
 *       <input data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="change" type="checkbox"/>
 *     </td>
 *    </tfoot>
 * </table>
 * ```
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

  /** Internal tracking of last clicked for shift+click behavior */
  lastChanged?: HTMLElement | null;

  /** Internal tracking of whether the shift key is active for multiple selection */
  shiftActive?: boolean;

  /**
   * On creation, ensure that the select all checkboxes are in sync.
   * Set up the event listeners for shift+click behavior.
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
    group: string | null = null,
    targets: HTMLInputElement[] = this.itemTargets,
    paramAttr = `data-${this.identifier}-group-param`,
  ): HTMLInputElement[] {
    const activeTargets = targets.filter(({ disabled }) => !disabled);

    if (!group) return activeTargets;

    const groups = group.split(' ');
    return activeTargets.filter((target) => {
      const targetGroups = new Set(
        (target.getAttribute(paramAttr) || '').split(' '),
      );
      return groups.some(targetGroups.has.bind(targetGroups));
    });
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
  toggle(event?: CustomEvent<ToggleOptions> & { params?: ToggleOptions }) {
    const { group = null } = { ...event?.detail, ...event?.params };
    const activeItems = this.getValidTargets(group);
    const lastChanged = this.lastChanged;

    if (this.shiftActive && lastChanged instanceof HTMLElement) {
      this.shiftActive = false;

      const lastClickedIndex = activeItems.findIndex(
        (item) => item === lastChanged,
      );

      // The last clicked item is not in the current group, skip bulk toggling
      if (lastClickedIndex === -1) return;

      const currentIndex = activeItems.findIndex(
        (item) => item === event?.target,
      );

      const [start, end] = [lastClickedIndex, currentIndex].sort(
        // eslint-disable-next-line id-length
        (a, b) => a - b,
      );

      activeItems.forEach((target, index) => {
        if (index >= start && index <= end) {
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

    this.getValidTargets(group, this.allTargets).forEach((target) => {
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
    const { force = null, group = null } = {
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

    this.getValidTargets(group).forEach((target) => {
      if (target.checked !== isChecked) {
        target.checked = isChecked;
        target.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    this.toggle(event);
  }

  disconnect() {
    document?.removeEventListener('keydown', this.handleShiftKey);
    document?.removeEventListener('keyup', this.handleShiftKey);
  }
}
