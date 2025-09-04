/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["disabled"] }] */

import { Controller } from '@hotwired/stimulus';

import { debounce } from '../utils/debounce';
import { forceFocus } from '../utils/forceFocus';
import { runInlineScripts } from '../utils/runInlineScripts';
import { transition } from '../utils/transition';

/**
 * Adds the ability for a dynamic, expanding, formset leveraging the Django
 * formset system of inputs and management fields.
 *
 * @example
 * ```html
 * <form data-controller="w-formset">
 *   <input type="hidden" name="form-TOTAL_FORMS" value="2" data-w-formset-target="totalFormsInput">
 *   <input type="hidden" name="form-MIN_NUM_FORMS" value="0" data-w-formset-target="minFormsInput">
 *   <input type="hidden" name="form-MAX_NUM_FORMS" value="50" data-w-formset-target="maxFormsInput">
 *   <input type="hidden" name="form-INITIAL_FORMS" value="2">
 *   <ul data-w-formset-target="forms">
 *     <li data-w-formset-target="child">
 *       <input type="text" name="form-0-name">
 *       <input type="hidden" name="form-0-DELETE" data-w-formset-target="deleteInput">
 *       <button type="button" data-action="w-formset#delete" data-w-formset-target="delete">Delete</button>
 *     </li>
 *     <li data-w-formset-target="child">
 *       <input type="text" name="form-1-name">
 *       <input type="hidden" name="form-1-DELETE" data-w-formset-target="deleteInput">
 *       <button type="button" data-action="w-formset#delete" data-w-formset-target="delete">Delete</button>
 *     </li>
 *   </ul>
 *   <button type="button" data-action="w-formset#add" data-w-formset-target="add">Add</button>
 *   <template data-w-formset-target="template">
 *     <li data-w-formset-target="child">
 *       <input type="text" name="form-__prefix__-name">
 *       <input type="hidden" name="form-__prefix__-DELETE" data-w-formset-target="deleteInput">
 *       <button type="button" data-action="w-formset#delete" data-w-formset-target="delete">Delete</button>
 *     </li>
 *   </template>
 * </form>
 * ```
 */
export class FormsetController extends Controller<HTMLElement> {
  static classes = ['deleted'];

  static targets = [
    'add',
    'child',
    'delete',
    'deleted',
    'deleteInput',
    'forms',
    'minFormsInput',
    'maxFormsInput',
    'orderInput',
    'template',
    'totalFormsInput',
  ];

  static values = {
    min: { default: 0, Number },
    max: { default: 1000, Number },
    total: { default: 0, Number },
  };

  /** Elements that trigger the adding of a child. */
  declare readonly addTargets: HTMLButtonElement[];
  /** Active child form elements. */
  declare readonly childTargets: HTMLElement[];
  /** Elements that trigger the deleting of a child. */
  declare readonly deleteTargets: HTMLButtonElement[];
  /** Classes to append when transitioning from an active child to a deleted form. */
  declare readonly deletedClasses: string[];
  /** Tracking of deleted child form elements. */
  declare readonly deletedTargets: HTMLElement[];
  /** Hidden input to track whether a specific form has been removed. */
  declare readonly deleteInputTargets: HTMLInputElement[];
  /** Target element to append new child forms to. */
  declare readonly formsTarget: HTMLElement;
  /** Hidden input to read for the value for min forms. */
  declare readonly minFormsInputTarget: HTMLInputElement;
  /** Hidden input to read for the value for max forms. */
  declare readonly maxFormsInputTarget: HTMLInputElement;
  /** Hidden input to track a specific form's order, if ordering is enabled. */
  declare readonly orderInputTargets: HTMLInputElement[];
  /** Target element that has the template content to clone for new forms.
   * `__prefix__` will be replaced with the next formIndex value upon creation. */
  declare readonly templateTarget: HTMLTemplateElement;
  /** Hidden input to track the total forms (including deleted) for POST request and initial reading. */
  declare readonly totalFormsInputTarget: HTMLInputElement;
  /** Set to the value to the management field MIN_NUM_FORMS. */
  declare minValue: number;
  /** Set to the value to the management field MAX_NUM_FORMS. */
  declare maxValue: number;
  /** Value tracking for the total amount of forms either active or deleted. */
  declare totalValue: number;

  elementPrefixRegex = /__prefix__(.*?['"])/g;

  initialize() {
    this.syncOrdering = debounce(this.syncOrdering.bind(this), 50);
    this.totalValue = parseInt(this.totalFormsInputTarget.value, 10);
    this.minValue = parseInt(this.minFormsInputTarget.value, 10);
    this.maxValue = parseInt(this.maxFormsInputTarget.value, 10);
  }

  /**
   * Ensure that any deleted children are hidden when connected (from HTML POST response)
   * and remove any error message elements so that it doesn't count towards the number
   * of errors on the tab at the top of the page.
   * @todo - check this actually works for any timing issues from w-count controller.
   */
  connect() {
    this.deletedTargets.forEach((target) => {
      target.classList.add(...this.deletedClasses);
      target.querySelectorAll('.error-message').forEach((el) => el.remove());
    });

    this.syncOrdering();

    this.dispatch('ready', {
      cancelable: false,
      detail: {
        minValue: this.minValue,
        maxValue: this.maxValue,
        totalValue: this.totalValue,
      },
    });
  }

  /**
   * Add a new child form from the template content and set focus to it.
   */
  add() {
    if (this.childTargets.length >= this.maxValue) return;

    if (
      this.dispatch('adding', {
        cancelable: true,
        detail: { formIndex: this.totalValue },
      }).defaultPrevented
    ) {
      return;
    }

    forceFocus(this.formsTarget.appendChild(this.newChild));
  }

  /**
   * Find the event's target's closest child target and remove it by
   * removing the 'child' target and adding a 'child-removed' target.
   *
   * @throws {Error} If the child form target for the event target cannot be found.
   */
  delete(event: Event) {
    const target = this.childTargets.find((child) =>
      child.contains(event.target as Node),
    );

    if (!target) {
      throw new Error(
        `Could not find child form target for event target: ${event.target}.`,
      );
    }

    if (this.childTargets.length <= this.minValue) return;

    if (
      this.dispatch('removing', { target, cancelable: true }).defaultPrevented
    ) {
      return;
    }

    const targetAttrName = `data-${this.identifier}-target`;

    target.setAttribute(
      targetAttrName,
      (target.getAttribute(targetAttrName)?.split(' ') ?? [])
        .concat(['deleted'])
        .join(' '),
    );
  }

  /**
   * When a new child is added, or one has been inserted after a re-ordering event,
   * update the total count and dispatch an added event (only when it is a new one).
   */
  childTargetConnected(target: HTMLElement) {
    this.syncOrdering();

    const totalFormsCount =
      this.childTargets.length + this.deletedTargets.length;
    if (totalFormsCount === this.totalValue) return;

    this.totalValue = totalFormsCount;

    this.dispatch('added', {
      target,
      cancelable: false,
      detail: { formIndex: totalFormsCount - 1 },
    });
  }

  /**
   * When removed, add the class and update the total count.
   * Only run if the target was previously a child (non-deleted) target.
   * Also update the DELETE input for this form.
   *
   * @throws {Error} If the DELETE input target cannot be found within the removed form.
   */
  deletedTargetConnected(target: HTMLElement) {
    if (!this.childTargets.find((child) => child === target)) return;

    const targetAttrName = `data-${this.identifier}-target`;

    target.setAttribute(
      targetAttrName,
      (target.getAttribute(targetAttrName)?.split(' ') ?? [])
        .filter((name) => name !== 'child')
        .join(' '),
    );

    const deletedClasses = this.deletedClasses;

    target.classList.add(...deletedClasses);
    transition(
      target,
      // If there are no classes to add, we can skip the delay before hiding.
      deletedClasses.length ? {} : { maxDelay: 0 },
    ).then(() => {
      target.setAttribute('hidden', '');
      this.dispatch('removed', { target, cancelable: false });
    });

    const deleteInput = this.deleteInputTargets.find((input) =>
      target.contains(input),
    );

    if (!deleteInput) {
      throw new Error(
        `Could not find "deleteInput" target within removed form. ${target.nodeName} with id '${target.id}'.`,
      );
    }

    if (deleteInput.value === '1') return;

    deleteInput.value = '1';

    // Update button states after deletion
    const activeCount = this.childTargets.length;
    const disableAdd = activeCount >= this.maxValue;
    const disableDelete = activeCount <= this.minValue;

    this.addTargets.forEach((button) => {
      button.disabled = disableAdd;
    });

    this.deleteTargets.forEach((button) => {
      button.disabled = disableDelete;
    });

    this.dispatch('change', {
      prefix: '',
      target: deleteInput,
      cancelable: false,
    });

    this.syncOrdering();
  }

  /**
   * When the totalValue changes, update the management fields and dispatch
   * a change event for the TOTAL_FORMS input.
   *
   * Disable any add or delete buttons based on the min/max values and current total,
   * even if the total value has not changed (e.g. on initial load).
   */
  totalValueChanged(currentValue: number, previousValue: number | undefined) {
    if (currentValue === previousValue || previousValue === undefined) return;
    const totalFormsInput = this.totalFormsInputTarget;

    const disableAdd = currentValue >= this.maxValue;
    const disableDelete = currentValue <= this.minValue;

    this.addTargets.forEach((button) => {
      button.disabled = disableAdd;
    });

    this.deleteTargets.forEach((button) => {
      button.disabled = disableDelete;
    });

    if (totalFormsInput.value === `${currentValue}`) return;

    totalFormsInput.value = `${currentValue}`;
    this.dispatch('change', {
      prefix: '',
      target: totalFormsInput,
      cancelable: false,
    });
  }

  /**
   * If the orderInputTargets are present, update the value of each input
   * to match the current order of the child elements.
   */
  syncOrdering() {
    const orderInputTargets = this.orderInputTargets;
    if (!orderInputTargets.length) return;

    let orderChanged = false;

    this.childTargets.forEach((child, index) => {
      const order = `${index + 1}`;

      const orderInput = orderInputTargets.find((input) =>
        child.contains(input),
      );

      if (!orderInput) {
        throw new Error(
          `Could not find "orderInput" target within form. ${child.nodeName} with id '${child.id}'.`,
        );
      }

      if (orderInput.value === order) return;

      orderChanged = true;

      orderInput.value = order;
      this.dispatch('change', {
        bubbles: true,
        cancelable: false,
        prefix: '',
        target: orderInput,
      });
    });

    if (orderChanged) {
      this.dispatch('ordered', {
        bubbles: true,
        cancelable: false,
      });
    }
  }

  /**
   * Prepare a new child element with the `__prefix__` values replaced with
   * the next formIndex value.
   */
  get newChild() {
    const element =
      this.templateTarget.content.firstElementChild?.cloneNode(true);

    if (!(element instanceof HTMLElement)) {
      throw new Error(`Invalid template content, must be a single node.`);
    }

    const formIndex = this.childTargets.length + this.deletedTargets.length;

    const newElement = document.createElement('template');
    newElement.innerHTML = element.outerHTML.replace(
      this.elementPrefixRegex,
      formIndex + '$1',
    );

    const newChildNode = newElement.content.firstElementChild?.cloneNode(
      true,
    ) as HTMLElement;

    runInlineScripts(newChildNode);

    return newChildNode;
  }
}
