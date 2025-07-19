import { Controller } from '@hotwired/stimulus';

const DEFAULT_CLASS = 'button-longrunning';

/**
 * Adds the ability for a button to be clicked and then not allow any further clicks
 * until the duration has elapsed. Will also update the button's label while in progress.
 *
 * @example
 * ```html
 * <button
 *   type="submit"
 *   class="button button-longrunning"
 *   data-controller="w-progress"
 *   data-w-progress-active-class="button-longrunning-active"
 *   data-w-progress-active-value="{% trans 'Signing in…' %}"
 *   data-w-progress-duration-seconds-value="40"
 *   data-action="w-progress#activate"
 * >
 *   {% icon name="spinner" %}
 *   <em data-w-progress-target="label">{% trans 'Sign in' %}</em>
 * </button>
 * ```
 */
export class ProgressController extends Controller<HTMLButtonElement> {
  static classes = ['active'];
  static targets = ['label'];
  static values = {
    active: { default: '', type: String },
    duration: { default: 30000, type: Number },
    label: { default: '', type: String },
    loading: { default: false, type: Boolean },
  };

  declare activeClass: string;
  /** Label to use when loading */
  declare activeValue: string;
  declare durationValue: number;
  /** Label to store the original text on the button */
  declare labelValue: string;
  declare loadingValue: boolean;
  declare readonly hasActiveClass: boolean;
  declare readonly hasLabelTarget: boolean;
  declare readonly labelTarget: HTMLElement;
  timer?: number;

  connect() {
    if (this.hasLabelTarget) return;
    const labelElement = this.element.querySelector('em');
    if (!labelElement) return;
    labelElement.setAttribute(`data-${this.identifier}-target`, 'label');
  }

  activate() {
    // If client-side validation is active on this form, and is going to block submission of the
    // form, don't activate the spinner
    const form = this.element.closest('form');

    if (
      form &&
      form.checkValidity &&
      !form.noValidate &&
      !form.checkValidity()
    ) {
      return;
    }

    window.setTimeout(() => {
      this.loadingValue = true;

      this.timer = window.setTimeout(() => {
        this.loadingValue = false;
      }, this.durationValue);
    });
  }

  deactivate() {
    this.loadingValue = false;

    if (this.timer) {
      clearTimeout(this.timer);
    }
  }

  loadingValueChanged(isLoading: boolean) {
    const activeClass = this.hasActiveClass
      ? this.activeClass
      : `${DEFAULT_CLASS}-active`;

    this.element.classList.toggle(activeClass, isLoading);

    if (!this.labelValue) {
      this.labelValue = this.hasLabelTarget
        ? (this.labelTarget.textContent as string)
        : (this.element.textContent as string);
    }

    if (isLoading) {
      // Disabling button must be done last: disabled buttons can't be
      // modified in the normal way, it would seem.
      this.element.setAttribute('disabled', '');

      if (this.activeValue && this.hasLabelTarget) {
        this.labelTarget.textContent = this.activeValue;
      }
    } else {
      this.element.removeAttribute('disabled');

      if (this.labelValue && this.hasLabelTarget) {
        this.labelTarget.textContent = this.labelValue;
      }
    }
  }

  disconnect(): void {
    this.deactivate();
  }
}
