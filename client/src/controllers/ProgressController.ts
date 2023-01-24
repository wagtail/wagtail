import { Application, Controller } from '@hotwired/stimulus';

const DEFAULT_CLASS = 'button-longrunning';

/**
 * Adds the ability for a button to be clicked and then not allow any further clicks
 * until the duration has elapsed. Will also update the button's label while in progress.
 *
 * @example
 * <button
 *   type="submit"
 *   class="button button-longrunning"
 *   data-controller="w-progress"
 *   data-w-progress-active-class="button-longrunning-active"
 *   data-w-progress-active-value="{% trans 'Signing in…' %}"
 *   data-w-progress-duration-seconds-value="40"
 *   data-action="w-progress#activate"
 * >
 *  {% icon name="spinner" %}
 *  <em data-w-progress-target="label">{% trans 'Sign in' %}</em>
 * </button>
 */
export class ProgressController extends Controller {
  static classes = ['active'];
  static targets = ['label'];
  static values = {
    active: { default: '', type: String },
    durationSeconds: { default: 30, type: Number },
    label: { default: '', type: String },
    loading: { default: false, type: Boolean },
  };

  declare activeClass: string;
  /** Label to use when loading */
  declare activeValue: string;
  declare durationSecondsValue: number;
  /** Label to store the original text on the button */
  declare labelValue: string;
  declare loadingValue: boolean;
  declare readonly hasActiveClass: boolean;
  declare readonly hasLabelTarget: boolean;
  declare readonly labelTarget: HTMLElement;
  timer?: number;

  /**
   * Ensure we have backwards compatibility with buttons that have
   * not yet adopted the new data attribute syntax.
   * Will warn and advise in release notes that this support
   * will be removed in a future version.
   * @deprecated - RemovedInWagtail60
   */
  static afterLoad(identifier: string, application: Application) {
    const { controllerAttribute } = application.schema;
    const { actionAttribute } = application.schema;

    document.addEventListener(
      'DOMContentLoaded',
      () => {
        document
          .querySelectorAll(
            `.${DEFAULT_CLASS}:not([${controllerAttribute}~='${identifier}'])`,
          )
          .forEach((button) => {
            button.setAttribute(controllerAttribute, identifier);
            button.setAttribute(actionAttribute, `${identifier}#activate`);

            const activeText = button.getAttribute('data-clicked-text');
            if (activeText) {
              button.setAttribute(
                `data-${identifier}-active-value`,
                activeText,
              );
              button.removeAttribute('data-clicked-text');
            }

            const labelElement = button.querySelector('em');
            if (labelElement) {
              labelElement.setAttribute(`data-${identifier}-target`, 'label');
            }

            button.setAttribute(
              `data-${identifier}-duration-seconds-value`,
              '30',
            );
          });
      },
      { once: true, passive: true },
    );
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

      const durationMs = this.durationSecondsValue * 1000;

      this.timer = window.setTimeout(() => {
        this.loadingValue = false;
      }, durationMs);
    });
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
    if (this.timer) {
      clearTimeout(this.timer);
    }
  }
}
