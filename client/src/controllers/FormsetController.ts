import { Controller } from '@hotwired/stimulus';

import { transition } from '../utils/transition';
import { runInlineScripts } from '../utils/runInlineScripts';

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
 *       <button type="button" data-action="w-formset#delete">Delete</button>
 *     </li>
 *     <li data-w-formset-target="child">
 *       <input type="text" name="form-1-name">
 *       <input type="hidden" name="form-1-DELETE" data-w-formset-target="deleteInput">
 *       <button type="button" data-action="w-formset#delete">Delete</button>
 *     </li>
 *   </ul>
 *   <button type="button" data-action="w-formset#add">Add</button>
 *   <template data-w-formset-target="template">
 *     <li data-w-formset-target="child">
 *       <input type="text" name="form-__prefix__-name">
 *       <input type="hidden" name="form-__prefix__-DELETE" data-w-formset-target="deleteInput">
 *       <button type="button" data-action="w-formset#delete">Delete</button>
 *     </li>
 *   </template>
 * </form>
 * ```
 */
export class FormsetController extends Controller<HTMLElement> {
  static classes = ['deleted'];

  static targets = [
    'child',
    'deleted',
    'deleteInput',
    'forms',
    'minFormsInput',
    'maxFormsInput',
    'template',
    'totalFormsInput',
  ];

  static values = {
    min: { default: 0, Number },
    max: { default: 1000, Number },
    total: { default: 0, Number },
  };

  /** Active child form elements. */
  declare readonly childTargets: HTMLElement[];
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
    this.totalValue = parseInt(this.totalFormsInputTarget.value, 10);
    this.minValue = parseInt(this.minFormsInputTarget.value, 10);
    this.maxValue = parseInt(this.maxFormsInputTarget.value, 10);
  }

  connect() {
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
   * Add a new child form from the template content.
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

    this.formsTarget.appendChild(this.newChild);
  }

  /**
   * Find the event's target's closest child target and remove it by
   * removing the 'child' target and adding a 'child-removed' target.
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
        .filter((name) => name !== 'child')
        .concat(['deleted'])
        .join(' '),
    );
  }

  /**
   * When a new child is added, update the total count and dispatch an added event.
   */
  childTargetConnected(target: HTMLElement) {
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
   * Also update the DELETE input for this form.
   */
  childTargetDisconnected(target: HTMLElement) {
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
    this.dispatch('change', {
      prefix: '',
      target: deleteInput,
      cancelable: false,
    });
  }

  /**
   * When the totalValue changes, update the management fields and dispatch
   * a change event for the TOTAL_FORMS input.
   */
  totalValueChanged(currentValue: number, previousValue: number | undefined) {
    if (currentValue === previousValue || previousValue === undefined) return;
    const totalFormsInput = this.totalFormsInputTarget;

    if (totalFormsInput.value === `${currentValue}`) return;

    totalFormsInput.value = `${currentValue}`;
    this.dispatch('change', {
      prefix: '',
      target: totalFormsInput,
      cancelable: false,
    });
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
