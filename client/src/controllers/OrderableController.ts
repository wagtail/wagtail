import { Controller } from '@hotwired/stimulus';
import Sortable from 'sortablejs';

enum Direction {
  Up = 'UP',
  Down = 'DOWN',
}

/**
 * Enables the ability for drag & drop or manual re-ordering of elements
 * within a prescribed container or the controlled element.
 *
 * Once re-ordering is completed an async request will be made to the
 * provided URL to submit the update per item.
 *
 * @example
 * ```html
 * <fieldset data-controller="w-orderable" data-w-orderable-url-value="/path/to/orderable/">
 *   <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="1" value="Item 1"/>
 *   <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="2" value="Item 2"/>
 *   <input type="button" data-w-orderable-target="item" data-w-orderable-item-id="3" value="Item 3"/>
 * </fieldset>
 * ```
 */
export class OrderableController extends Controller<HTMLElement> {
  static classes = ['active', 'chosen', 'drag', 'ghost'];
  static targets = ['handle', 'item'];
  static values = {
    animation: { default: 200, type: Number },
    container: { default: '', type: String },
    message: { default: '', type: String },
    url: String,
  };

  declare readonly handleTarget: HTMLElement;
  declare readonly itemTarget: HTMLElement;

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
  /** Base URL template to use for submitting an updated order for a specific item. */
  declare urlValue: string;

  order: string[];
  sortable: ReturnType<typeof Sortable.create>;

  constructor(context) {
    super(context);
    this.order = [];
  }

  connect() {
    const containerSelector = this.containerValue;
    const container = ((containerSelector &&
      this.element.querySelector(containerSelector)) ||
      this.element) as HTMLElement;

    this.sortable = Sortable.create(container, this.options);
    this.order = this.sortable.toArray();

    this.dispatch('ready', {
      cancelable: false,
      detail: { order: this.order },
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
        item,
        newIndex,
        oldIndex,
      }: {
        item: HTMLElement;
        oldIndex: number;
        newIndex: number;
      }) => {
        this.element.classList.remove(...this.activeClasses);
        if (oldIndex === newIndex) return;
        this.order = this.sortable.toArray();
        this.submit({ ...this.getItemData(item), newIndex });
      },
    };
  }

  getItemData(target: EventTarget | null) {
    const identifier = this.identifier;
    const item =
      target instanceof HTMLElement &&
      target.closest(`[data-${identifier}-target='item']`);

    if (!item) return { id: '', label: '' };

    return {
      id: item.getAttribute(`data-${identifier}-item-id`) || '',
      label: item.getAttribute(`data-${identifier}-item-label`) || '',
    };
  }

  /**
   * Applies a manual move using up/down methods.
   */
  apply({ currentTarget }: Event) {
    const { id, label } = this.getItemData(currentTarget);
    const newIndex = this.order.indexOf(id);
    this.submit({ id, label, newIndex });
  }

  /**
   * Calculate a manual move either up or down and prepare the Sortable
   * data for re-ordering.
   */
  move({ currentTarget }: Event, direction: Direction) {
    const identifier = this.identifier;
    const item =
      currentTarget instanceof HTMLElement &&
      currentTarget.closest(`[data-${identifier}-target='item']`);

    if (!item) return;

    const id = item.getAttribute(`data-${identifier}-item-id`) || '';
    const newIndex = this.order.indexOf(id);

    this.order.splice(newIndex, 1);

    if (direction === Direction.Down) {
      this.order.splice(newIndex + 1, 0, id);
    } else if (direction === Direction.Up && newIndex > 0) {
      this.order.splice(newIndex - 1, 0, id);
    } else {
      this.order.splice(newIndex, 0, id); // to stop at the top
    }

    this.sortable.sort(this.order, true);
  }

  /**
   * Manually move up visually but do not submit to the server.
   */
  up(event: KeyboardEvent) {
    this.move(event, Direction.Up);
    (event.currentTarget as HTMLButtonElement)?.focus();
  }

  /**
   * Manually move down visually but do not submit to the server.
   */
  down(event: KeyboardEvent) {
    this.move(event, Direction.Down);
    (event.currentTarget as HTMLButtonElement)?.focus();
  }

  /**
   * Submit an updated ordering to the server.
   */
  submit({
    id,
    label,
    newIndex,
  }: {
    id: string;
    label: string;
    newIndex: number;
  }) {
    let url = this.urlValue.replace('999999', id);
    if (newIndex !== null) {
      url += '?position=' + newIndex;
    }

    const message = (this.messageValue || '__LABEL__').replace(
      '__LABEL__',
      label,
    );

    const formElement = this.element.closest('form');

    const CSRFElement =
      formElement &&
      formElement.querySelector('input[name="csrfmiddlewaretoken"]');

    if (CSRFElement instanceof HTMLInputElement) {
      const CSRFToken: string = CSRFElement.value;
      const body = new FormData();

      body.append('csrfmiddlewaretoken', CSRFToken);

      fetch(url, { method: 'POST', body })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
        })
        .then(() => {
          this.dispatch('w-messages:add', {
            prefix: '',
            target: window.document,
            detail: { clear: true, text: message, type: 'success' },
            cancelable: false,
          });
        })
        .catch((error) => {
          throw error;
        });
    }
  }

  disconnect() {
    if (this.sortable) {
      this.sortable.destroy();
    }
  }
}
