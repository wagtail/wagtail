import { Controller } from '@hotwired/stimulus';
import { debounce, DebouncedFunction } from '../utils/debounce';
import { setOptionalInterval } from '../utils/interval';

const DEFAULT_DURATIONS = {
  initial: 2_000,
  notify: 30,
  check: 500,
};

export type Durations = typeof DEFAULT_DURATIONS;

/**
 * Enables the controlled form to support prompting the user when they
 * are about to move away from the page with potentially unsaved changes.
 *
 * @example - Warn the user when there are unsaved edits
 * ```html
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
 *   data-w-unsaved-confirmation-value="true"
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 * ```
 *
 * @example - Force the confirmation dialog
 * ```html
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
 *   data-w-unsaved-confirmation-value="true"
 *   data-w-unsaved-force-value="true"
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 * ```
 */
export class UnsavedController extends Controller<HTMLFormElement> {
  static values = {
    confirmation: { default: false, type: Boolean },
    durations: { default: DEFAULT_DURATIONS, type: Object },
    force: { default: false, type: Boolean },
    hasEdits: { default: false, type: Boolean },
  };

  /** Whether to show the browser confirmation dialog. */
  declare confirmationValue: boolean;
  /** Configurable duration values. */
  declare durationsValue: Durations;
  /**
   * When set to `true`, the initial form will always be considered dirty.
   * Useful for when the user just submitted an invalid form, in which case we
   * consider the form to be dirty even on initial load.
   *
   * Note that the `confirmationValue` must still be set to `true` in order for
   * the browser confirmation dialog to appear.
   */
  declare forceValue: boolean;
  /** Whether there are unsaved edits in the form. */
  declare hasEditsValue: boolean;

  /** Serialized data of the initially rendered form. */
  initialFormData?: string;
  /** Previous serialized form data for continuous change detection. */
  previousFormData?: string;
  /** Interval ID for periodic change checks. */
  checkInterval: ReturnType<typeof setOptionalInterval> = null;

  declare setInitialFormDataLazy: DebouncedFunction<[], void>;

  initialize() {
    this.check = this.check.bind(this);
    this.notify = this.notify.bind(this);
    this.setInitialFormData = this.setInitialFormData.bind(this);
  }

  connect() {
    this.dispatch('ready', { cancelable: false });
  }

  /**
   * Resolve the form's `formData` into a comparable string with any
   * unrelated data cleaned from the value.
   *
   * Include handling of File field data to determine a comparable value.
   * @see https://developer.mozilla.org/en-US/docs/Web/API/File
   */
  get formData() {
    const exclude = ['csrfmiddlewaretoken', 'next'];
    const formData = new FormData(this.element);
    exclude.forEach((key) => formData.delete(key));

    // Replace File objects with a comparable representation
    for (const key of formData.keys()) {
      if (formData.get(key) instanceof File) {
        // Use getAll to handle multi-file inputs
        const files = formData.getAll(key).flatMap((file: File) => [
          ['name', file.name],
          ['size', `${file.size}`],
          ['type', file.type],
        ]);
        formData.set(key, new URLSearchParams(files).toString());
      }
    }

    // Convert FormData to string for comparison, using URLSearchParams
    // instead of JSON.stringify() to handle multi-valued fields.
    return new URLSearchParams(
      // FormData may contain File objects, but we've converted them above.
      // https://github.com/microsoft/TypeScript/issues/30584
      formData as unknown as Record<string, string>,
    ).toString();
  }

  /**
   * Checks whether the form data has changed since the last call to this method.
   * @returns whether the form data has changed
   */
  hasChanges() {
    // Don't start checking for changes until the initial form data is set
    if (!this.initialFormData) return false;

    const newPayload = this.formData;
    const changed = this.previousFormData !== newPayload;
    this.hasEditsValue = this.forceValue || this.initialFormData !== newPayload;
    this.previousFormData = newPayload;
    return changed;
  }

  /**
   * Check for changes in the form data and notify if there are any.
   */
  check() {
    if (this.hasChanges()) this.notify();
  }

  durationsValueChanged(newDurations: Durations, oldDurations?: Durations) {
    if (this.forceValue) {
      this.hasEditsValue = true;
      return;
    }

    if (
      !this.initialFormData &&
      newDurations.initial !== oldDurations?.initial
    ) {
      // Set up the initial form data with the initial delay to allow other
      // initializations to complete first. We do this in durationsValueChanged
      // to allow other code to change the delay value before the initial setup.

      // Cancel any debounced calls and set up a new one with the new delay
      if (this.setInitialFormDataLazy) {
        this.setInitialFormDataLazy.cancel();
      }
      this.setInitialFormDataLazy = debounce(
        this.setInitialFormData,
        newDurations.initial,
      );

      this.setInitialFormDataLazy();
    }

    if (newDurations.check !== oldDurations?.check) {
      // Reset the check interval with the new check duration
      if (this.checkInterval) {
        clearInterval(this.checkInterval);
      }
      this.checkInterval = setOptionalInterval(this.check, newDurations.check);
    }

    // Ensure we wait until at least the next check interval, so we only
    // notify if there are no further consecutive changes.
    const newNotifyDuration = newDurations.notify + newDurations.check;
    const oldNotifyDuration =
      (oldDurations?.notify || 0) + (oldDurations?.check || 0);

    if (newNotifyDuration !== oldNotifyDuration) {
      // Reset the debounced notify with the new duration
      if ('restore' in this.notify) {
        this.notify.cancel();
        this.notify = this.notify.restore();
      }
      this.notify = debounce(this.notify, newNotifyDuration);
    }
  }

  /**
   * Take a snapshot of the current form data to use as the initial state
   * for change detection.
   */
  setInitialFormData() {
    const initialFormData = this.formData;
    this.initialFormData = initialFormData;
    this.previousFormData = initialFormData;
    this.dispatch('watch-edits', {
      cancelable: false,
      detail: { initialFormData },
    });
  }

  /**
   * Clear the tracking changes values and messages.
   */
  clear() {
    this.setInitialFormData();
    this.hasEditsValue = false;
    this.forceValue = false;
  }

  /**
   * Trigger the beforeunload confirmation dialog if active (confirm value is true).
   * @see https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event
   */
  confirm(event: BeforeUnloadEvent) {
    if (!this.confirmationValue) return;

    if (this.hasEditsValue) {
      // Dispatch a `confirm` event that is cancelable to allow for custom handling
      // instead of the browser's default confirmation dialog.
      const confirmEvent = this.dispatch('confirm', { cancelable: true });
      if (confirmEvent.defaultPrevented) return;

      // This will trigger the browser's default confirmation dialog
      event.preventDefault();
    }
  }

  hasEditsValueChanged(current: boolean, previous: boolean) {
    if (current !== previous) this.notify();
  }

  /**
   * Notify the user of changes to the form.
   * Dispatch events to update the footer message via dispatching events.
   */
  notify: (() => void) | DebouncedFunction<[], void> = () => {
    const edits = this.hasEditsValue;

    if (!edits) {
      this.dispatch('clear', { cancelable: false });
      return;
    }

    this.dispatch('add', { cancelable: false, detail: { type: 'edits' } });
  };

  /**
   * When the form is submitted, ensure that the exit confirmation
   * does not trigger. Deactivate the confirmation by setting the
   * confirmation value to false.
   */
  submit() {
    this.confirmationValue = false;
  }

  disconnect() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }
}
