import { Controller } from '@hotwired/stimulus';
import { debounce, DebouncibleFunction } from '../utils/debounce';
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
    checkInterval: { default: 500, type: Number },
    confirmation: { default: false, type: Boolean },
    force: { default: false, type: Boolean },
    hasComments: { default: false, type: Boolean },
    hasEdits: { default: false, type: Boolean },
  };

  /**
   * Initial delay before setting up the check interval to allow other
   * initializations to complete, in milliseconds.
   */
  static initialDelayValue = 2_000;
  /** Delay before notifying about changes, in milliseconds. */
  static notifyDelayValue = 30;

  /** Duration between change checks, in milliseconds. */
  declare checkIntervalValue: number;
  /** Whether to show the browser confirmation dialog. */
  declare confirmationValue: boolean;
  /**
   * When set to `true`, the initial form will always be considered dirty.
   * Useful for when the user just submitted an invalid form, in which case we
   * consider the form to be dirty even on initial load.
   *
   * Note that the `confirmationValue` must still be set to `true` in order for
   * the browser confirmation dialog to appear.
   */
  declare forceValue: boolean;
  /** Whether there are unsaved comment changes in the form. */
  declare hasCommentsValue: boolean;
  /** Whether there are unsaved edits in the form. */
  declare hasEditsValue: boolean;

  /** Serialized data of the initially rendered form. */
  initialFormData?: string;
  /** Previous serialized form data for continuous change detection. */
  previousFormData?: string;
  /** Interval ID for periodic change checks. */
  checkInterval: ReturnType<typeof setOptionalInterval> = null;

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
    const exclude = [
      'csrfmiddlewaretoken',
      'loaded_revision_id',
      'loaded_revision_created_at',
      'next',
    ];
    const formData = new FormData(this.element);
    exclude.forEach((key) => formData.delete(key));

    // Replace File objects with a comparable representation
    // and remove comment form data as it's handled separately
    for (const key of [...formData.keys()]) {
      if (key.startsWith('comments-')) {
        formData.delete(key);
      } else if (formData.get(key) instanceof File) {
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
    const { commentApp } = window.comments || {};
    const hasComments = !!commentApp?.selectors.selectIsDirty(
      commentApp?.store.getState(),
    );

    // Consider the form changed if
    const changed =
      // the current form data (without comments) differs from the previous check
      this.previousFormData !== newPayload ||
      // or if the comment dirty state has changed from `false` to `true`
      (hasComments && !this.hasCommentsValue);

    this.hasEditsValue = this.forceValue || this.initialFormData !== newPayload;
    this.hasCommentsValue = hasComments;
    this.previousFormData = newPayload;
    return changed;
  }

  /**
   * Check for changes in the form data and notify if there are any.
   */
  check() {
    if (this.hasChanges()) this.notify();
  }

  checkIntervalValueChanged(newInterval: number) {
    if (this.forceValue) {
      this.hasEditsValue = true;
      return;
    }

    if (!this.initialFormData) {
      // Set up the initial form data with the initial delay to allow other
      // initializations to complete first.
      debounce(this.setInitialFormData, UnsavedController.initialDelayValue)();
    }

    // Reset the check interval with the new value
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
    this.checkInterval = setOptionalInterval(this.check, newInterval);

    // Ensure we wait until at least the next check interval, so we only
    // notify if there are no further consecutive changes.
    const newNotifyDuration = newInterval + UnsavedController.notifyDelayValue;

    // Reset the debounced notify with the new duration
    if ('restore' in this.notify) {
      this.notify.cancel();
      this.notify = this.notify.restore();
    }
    this.notify = debounce(this.notify, newNotifyDuration);
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
    this.hasCommentsValue = false;
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
  notify: DebouncibleFunction<() => void> = () => {
    if (!this.hasEditsValue && !this.hasCommentsValue) {
      this.dispatch('clear', { cancelable: false });
      return;
    }

    this.dispatch('add', { cancelable: true, detail: { type: 'edits' } });
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
