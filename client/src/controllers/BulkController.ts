import { Controller } from '@hotwired/stimulus';
/**
 * Adds the ability to collectively toggle a set of (non-disabled) checkboxes.
 *
 * @example
 * <div data-controller="w-bulk">
 *   <input type="checkbox" data-action="w-bulk#toggleAll" data-w-bulk-target="all">
 *   <div>
 *     <input type="checkbox" data-action="w-bulk#change" data-w-bulk-target="item" disabled>
 *     <input type="checkbox" data-action="w-bulk#change" data-w-bulk-target="item">
 *     <input type="checkbox" data-action="w-bulk#change" data-w-bulk-target="item">
 *   </div>
 *   <button data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
 *   <button data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
 * </div>
 */
export class BulkController extends Controller<HTMLElement> {
  static targets = ['all', 'item'];

  /** All select-all checkbox targets */
  declare readonly allTargets: HTMLInputElement[];

  /** All item checkbox targets */
  declare readonly itemTargets: HTMLInputElement[];

  get activeItems() {
    return this.itemTargets.filter(({ disabled }) => !disabled);
  }

  /**
   * On creation, ensure that the select all checkboxes are in sync.
   */
  connect() {
    this.toggle();
  }

  /**
   * When something is toggled, ensure the select all targets are kept in sync.
   */
  toggle() {
    const isAllChecked = !this.activeItems.some((item) => !item.checked);
    this.allTargets.forEach((target) => {
      // eslint-disable-next-line no-param-reassign
      target.checked = isAllChecked;
    });
  }

  /**
   * Toggles all item checkboxes based on select-all checkbox.
   */
  toggleAll(event: Event & { params?: { force?: boolean } }): void {
    const force = event?.params?.force;
    const checkbox = event.target as HTMLInputElement;
    const isChecked = typeof force === 'boolean' ? force : checkbox.checked;

    this.activeItems.forEach((target) => {
      if (target.checked !== isChecked) {
        // eslint-disable-next-line no-param-reassign
        target.checked = isChecked;
        target.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    this.toggle();
  }
}
