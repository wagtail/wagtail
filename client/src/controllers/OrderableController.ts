/* eslint no-param-reassign: ["error", { "ignorePropertyModificationsFor": ["disabled"] }] */

import { Controller } from '@hotwired/stimulus';
import Sortable from 'sortablejs';
import { debounce } from '../utils/debounce';
import { forceFocus } from '../utils/forceFocus';

enum Direction {
  Up = 'UP',
  Down = 'DOWN',
}

/**
 * Enables the ability for drag & drop or manual re-ordering of elements
 * within a prescribed container or the controlled element.
 *
 * If the url value is provided, the controller will submit the updated
 * order to the server via an async POST request once re-ordering is
 * completed (via drag & drop) or manually via calling the submit method.
 * This allows for granular keyboard control without submitting to the server
 * every change.
 *
 * @example
 * ```html
 * <fieldset data-controller="w-orderable" data-w-orderable-url-value="/path/to/orderable/">
 *  <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="1" value="Item 1"/>
 *  <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="2" value="Item 2"/>
 *  <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="3" value="Item 3"/>
 * </fieldset>
 * ```
 */
export class OrderableController extends Controller<HTMLElement> {
  static classes = ['active', 'chosen', 'drag', 'ghost'];
  static targets = ['container', 'handle', 'item', 'up', 'down'];
  static values = {
    animation: { default: 200, type: Number },
    container: { default: '', type: String },
    message: { default: '', type: String },
    name: { default: '', type: String },
    url: String,
  };

  declare readonly hasContainerTarget: boolean;
  declare readonly containerTarget: HTMLElement;
  declare readonly handleTargets: HTMLButtonElement[];
  declare readonly itemTargets: HTMLElement[];
  declare readonly upTargets: HTMLButtonElement[];
  declare readonly downTargets: HTMLButtonElement[];

  declare readonly activeClasses: string[];
  declare readonly chosenClass: string;
  declare readonly dragClass: string;
  declare readonly ghostClass: string;

  declare readonly hasChosenClass: boolean;
  declare readonly hasDragClass: boolean;
  declare readonly hasGhostClass: boolean;

  /** Transition animation duration for re-ordering. */
  declare animationValue: number;
  /** A selector to determine the container that will be the parent of the orderable elements. */
  declare containerValue: string;
  /** A translated message template for when the update is successful, replaces `__LABEL__` with item's title. */
  declare messageValue: string;
  /** The name of the controller instance, used to provide the contextual name for the HTML5 drag events, defaults to the identifier. */
  declare nameValue: string;
  /** Base URL template to use for submitting an updated order for a specific item. */
  declare urlValue: string;

  sortable: ReturnType<typeof Sortable.create>;

  initialize() {
    this.resetControls = debounce(this.resetControls.bind(this), 50);
  }

  connect() {
    const containerSelector = this.containerValue;
    const container = this.hasContainerTarget
      ? this.containerTarget
      : (((containerSelector &&
          this.element.querySelector(containerSelector)) ||
          this.element) as HTMLElement);

    this.sortable = Sortable.create(container, this.options);

    this.dispatch('ready', {
      cancelable: false,
      detail: { order: this.sortable.toArray() },
    });
  }

  get options() {
    const identifier = this.identifier;
    return {
      ...(this.hasGhostClass ? { ghostClass: this.ghostClass } : {}),
      ...(this.hasChosenClass ? { chosenClass: this.chosenClass } : {}),
      ...(this.hasDragClass ? { dragClass: this.dragClass } : {}),
      animation: this.animationValue,
      dataIdAttr: `data-${identifier}-item-id`,
      draggable: `[data-${identifier}-target="item"]`,
      handle: `[data-${identifier}-target="handle"]`,
      onStart: () => {
        this.element.classList.add(...this.activeClasses);
      },
      onEnd: ({
        item: currentTarget,
        newIndex,
        oldIndex,
      }: {
        item: HTMLElement;
        oldIndex: number;
        newIndex: number;
      }) => {
        this.element.classList.remove(...this.activeClasses);
        if (oldIndex === newIndex) return;
        this.resetControls();
        this.apply({ currentTarget }, newIndex);
        this.dispatch('ordered', { bubbles: true, cancelable: false });
      },
      setData: (dataTransfer) => {
        dataTransfer.setData(
          'application/vnd.wagtail.type',
          this.nameValue || this.identifier,
        );
      },
    };
  }

  /**
   * Apply the updated ordering to the server if the url value is provided,
   * dispatch events before & after the submission.
   */
  apply(
    { currentTarget }: { currentTarget: EventTarget | null },
    newIndexOverride?: number,
  ) {
    const urlValue = this.urlValue;
    if (!urlValue) return;

    const identifier = this.identifier;
    const item =
      currentTarget instanceof HTMLElement &&
      currentTarget.closest(`[data-${identifier}-target='item']`);

    if (!item) return;

    const id = item.getAttribute(`data-${identifier}-item-id`) || '';
    const label = item.getAttribute(`data-${identifier}-item-label`) || '';

    // todo - check the ?? is what I want here
    const newIndex = newIndexOverride ?? this.sortable.toArray().indexOf(id);

    const formElement = this.element.closest('form');

    const CSRFElement =
      formElement &&
      formElement.querySelector('input[name="csrfmiddlewaretoken"]');

    if (!(CSRFElement instanceof HTMLInputElement)) {
      throw new Error('CSRF token not found');
    }

    this.dispatch('submitting', {
      bubbles: true,
      cancelable: false,
      detail: { id, newIndex },
    });

    const CSRFToken: string = CSRFElement.value;

    const body = new FormData();
    body.append('csrfmiddlewaretoken', CSRFToken);

    const url = [
      urlValue.replace('999999', id),
      newIndex === null ? '' : `?position=${newIndex}`,
    ].join('');

    fetch(url, { method: 'POST', body })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
      })
      .then(() => {
        const message = (this.messageValue || '__LABEL__').replace(
          '__LABEL__',
          label,
        );

        this.dispatch('w-messages:add', {
          prefix: '',
          target: window.document,
          detail: { clear: true, text: message, type: 'success' },
          cancelable: false,
        });
      })
      .catch((error) => {
        throw error;
      })
      .finally(() => {
        this.dispatch('submitted', {
          bubbles: true,
          cancelable: false,
          detail: { id, newIndex },
        });
      });
  }

  /**
   * Calculate a manual move either up or down and re-order (sort) the elements
   * without applying to the server.
   */
  move({ currentTarget }: Event, direction: Direction) {
    const identifier = this.identifier;
    const item =
      currentTarget instanceof HTMLElement &&
      currentTarget.closest(`[data-${identifier}-target='item']`);

    if (!item) return;

    const id = item.getAttribute(`data-${identifier}-item-id`) || '';
    const order = this.sortable.toArray();

    const newIndex = order.indexOf(id);

    order.splice(newIndex, 1);

    if (direction === Direction.Down) {
      order.splice(newIndex + 1, 0, id);
    } else if (direction === Direction.Up && newIndex > 0) {
      order.splice(newIndex - 1, 0, id);
    } else {
      order.splice(newIndex, 0, id); // to stop at the top
    }

    // Do not re-order if the order is the same
    if (this.sortable.toArray().join() === order.join()) return;

    this.sortable.sort(order, true);
    this.resetControls();
    this.dispatch('ordered', { bubbles: true, cancelable: false });
  }

  /**
   * Manually move up visually but do not submit to the server,
   * keeping focus on the trigger element which may have moved around
   * in the DOM.
   */
  up(event: Event) {
    this.move(event, Direction.Up);
    forceFocus(event.currentTarget as HTMLElement);
  }

  /**
   * Manually move down visually but do not submit to the server,
   * keeping focus on the trigger element which may have moved around
   * in the DOM.
   */
  down(event: Event) {
    this.move(event, Direction.Down);
    forceFocus(event.currentTarget as HTMLElement);
  }

  /**
   * Reset the controls based on the current order of the items
   * so that any up, down or handle controls are disabled when
   * they are at the top or bottom of the list.
   */
  resetControls() {
    const handles = this.handleTargets;
    const upTargets = this.upTargets;
    const downTargets = this.downTargets;

    this.itemTargets
      .filter((item) => !item.hidden)
      .map((item) => ({
        handle: handles.find((handle) => item.contains(handle)),
        upControls: upTargets.filter((control) => item.contains(control)),
        downControls: downTargets.filter((control) => item.contains(control)),
      }))
      .forEach(({ handle, upControls, downControls }, index, targets) => {
        if (handle) {
          handle.disabled = targets.length === 1;
        }

        upControls.forEach((control) => {
          control.disabled = index === 0;
        });

        downControls.forEach((control) => {
          control.disabled = index === targets.length - 1;
        });
      });
  }

  itemTargetConnected() {
    this.resetControls();
  }

  itemTargetDisconnected() {
    this.resetControls();
  }

  disconnect() {
    if (this.sortable) {
      this.sortable.destroy();
    }
  }
}
