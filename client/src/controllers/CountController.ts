import { Controller } from '@hotwired/stimulus';
import { ngettext } from '../utils/gettext';

const DEFAULT_ERROR_SELECTOR = '.error-message,.help-critical';

/**
 * Adds the ability for a controlled element to update the total count
 * of selected elements (via the `find` selector) within the provided
 * container (via a selector or defaulting to the controlled element).
 *
 * @example - Finding all error messages within the body
 * ```html
 * <section>
 *   <div data-controller="w-count" data-w-count-container-value="body">
 *    <span data-w-count-target="label"></span>
 *    <span class="error-message">An error</span>
 *   </div>
 *   <div class="error-message">Another error</div>
 * </section>
 * ```
 *
 * @example - Change a class when the total is above the provided minimum in the controlled element
 * ```html
 * <form data-controller="w-count" data-w-count-min-value="1" data-w-count-active-class="active" data-w-count-find-value="*:checked">
 *   <input type="checkbox" name="opt" value="A" />
 *   <input type="checkbox" name="opt" value="B" checked="" />
 *   <input type="checkbox" name="opt" value="C" checked="" />
 * </form>
 * ```
 */
export class CountController extends Controller<HTMLFormElement> {
  static classes = ['active'];

  static targets = ['label', 'total'];

  static values = {
    container: { default: '', type: String },
    find: { default: DEFAULT_ERROR_SELECTOR, type: String },
    labels: { default: [], type: Array },
    min: { default: 0, type: Number },
    total: { default: 0, type: Number },
  };

  /** Selector string, used to determine the container/s to search through. If not provided will use the controller's element. */
  declare containerValue: string;
  /** Selector string, used to find the elements to count within the container. */
  declare findValue: string;
  /** Override pluralisation strings, e.g. `data-w-count-labels-value='["One item","Many items"]'`. */
  declare labelsValue: string[];
  /** Minimum value, anything equal or below will trigger blank labels in the UI. */
  declare minValue: number;
  /** Total current count of found elements. */
  declare totalValue: number;

  declare readonly activeClass: string;
  declare readonly hasActiveClass: boolean;
  declare readonly hasLabelTarget: boolean;
  declare readonly hasTotalTarget: boolean;
  declare readonly labelTarget: HTMLElement;
  declare readonly totalTarget: HTMLElement;

  connect() {
    this.count();
  }

  count() {
    const containerSelector = this.containerValue;

    const containers = containerSelector
      ? [...document.querySelectorAll(containerSelector)]
      : [this.element];

    this.totalValue = containers
      .map((element) => element.querySelectorAll(this.findValue).length)
      .reduce((total, subTotal) => total + subTotal, 0);

    return this.totalValue;
  }

  getLabel(total: number) {
    const defaultText = ngettext('%(num)s error', '%(num)s errors', total);

    if (this.labelsValue.length > 1) {
      const [single, plural = this.labelsValue[1], key = '__total__'] =
        this.labelsValue;
      return ngettext(single, plural, total).replace(key, `${total}`);
    }

    return defaultText.replace('%(num)s', `${total}`);
  }

  minValueChanged() {
    this.totalValueChanged(this.count());
  }

  totalValueChanged(total: number) {
    const min = this.minValue;
    if (this.hasActiveClass) {
      this.element.classList.toggle(this.activeClass, total > min);
    }
    if (this.hasLabelTarget) {
      this.labelTarget.textContent = total > min ? this.getLabel(total) : '';
    }
    if (this.hasTotalTarget) {
      this.totalTarget.textContent = total > min ? `${total}` : '';
    }
  }
}
