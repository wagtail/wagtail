import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';
import { domReady } from '../utils/domReady';

declare global {
  interface Window {
    comments: { commentApp: { selectors: any; store: any } };
    enableDirtyFormCheck: any;
  }
}

const DEFAULT_DURATIONS = {
  initial: 10_000,
  long: 3_000,
  notify: 30,
  short: 300,
};

/**
 * Enables the controlled form to support prompting the user when they
 * are about to move away from the page with potentially unsaved changes.
 *
 * @example - Warn the user when there are unsaved edits
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
 *   data-w-unsaved-confirmation-value="You have unsaved changes!"
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 *
 * @example - Watch comments for changes in addition to edits (default is edits only)
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
 *   data-w-unsaved-confirmation-value="You have unsaved changes!"
 *   data-w-unsaved-watch-value="edits comments"
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 *
 * @example - Force the confirmation dialog
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm change->w-unsaved#check"
 *   data-w-unsaved-confirmation-value="You have unsaved changes!"
 *   data-w-unsaved-force-value="true"
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 *
 * @example - Force the confirmation dialog without watching for edits/comments
 * <form
 *   data-controller="w-unsaved"
 *   data-action="w-unsaved#submit beforeunload@window->w-unsaved#confirm"
 *   data-w-unsaved-confirmation-value="Please double check before you close"
 *   data-w-unsaved-force-value="true"
 *   data-w-unsaved-watch-value=""
 * >
 *   <input type="text" value="something" />
 *   <button>Submit</submit>
 * </form>
 */
export class UnsavedController extends Controller<HTMLFormElement> {
  static values = {
    confirmation: { default: '', type: String },
    durations: { default: DEFAULT_DURATIONS, type: Object },
    force: { default: false, type: Boolean },
    hasComments: { default: false, type: Boolean },
    hasEdits: { default: false, type: Boolean },
    watch: { default: 'edits', type: String },
  };

  /** Translated value for the beforeunload confirmation dialog, if empty no confirmation will show. */
  declare confirmationValue: string;
  /** Configurable duration values. */
  declare durationsValue: typeof DEFAULT_DURATIONS;
  /** When set to true, the form will always be considered dirty and the confirmation dialog will be forced to show. */
  declare forceValue: boolean;
  /** Value (state) tracking of what changes exist (comments). */
  declare hasCommentsValue: boolean;
  /** Value (state) tracking of what changes exist (edits). */
  declare hasEditsValue: boolean;
  /** Determines what kinds of data will be watched, defaults to edits only. */
  declare watchValue: string;

  initialFormData?: string;
  observer?: MutationObserver;
  runningCheck?: ReturnType<typeof debounce>;

  initialize() {
    this.notify = debounce(this.notify.bind(this), this.durationsValue.notify);
  }

  connect() {
    this.clear();
    const durations = this.durationsValue;
    const watch = this.watchValue;

    if (watch.includes('comments')) this.watchComments(durations);
    if (watch.includes('edits')) this.watchEdits(durations);

    this.dispatch('ready', { cancelable: false });
  }

  /**
   * Resolve the form's `formData` into a comparable string without any comments
   * data included and other unrelated data cleaned from the value.
   *
   * Include handling of File field data to determine a comparable value.
   * @see https://developer.mozilla.org/en-US/docs/Web/API/File
   */
  get formData() {
    const exclude = ['comment_', 'comments-', 'csrfmiddlewaretoken', 'next'];
    const formData = new FormData(this.element);
    return JSON.stringify(
      [...formData.entries()].filter(
        ([key]) => !exclude.some((prefix) => key.startsWith(prefix)),
      ),
      (_key, value) =>
        value instanceof File
          ? { name: value.name, size: value.size, type: value.type }
          : value,
    );
  }

  /**
   * Check for edits to the form with a delay based on whether the form
   * currently has edits. If called multiple times, cancel & restart the
   * delay timer.
   *
   * Intentionally delay the check if there are already edits to the longer
   * delay so that the UX is improved. Users are unlikely to go back to an
   * original state of the form after making edits.
   */
  check() {
    const { long: longDuration, short: shortDuration } = this.durationsValue;

    if (this.runningCheck) {
      this.runningCheck.cancel();
    }

    this.runningCheck = debounce(
      () => {
        if (this.forceValue) {
          this.hasEditsValue = true;
          return;
        }

        if (!this.initialFormData) {
          this.hasEditsValue = false;
          return;
        }

        this.hasEditsValue = this.initialFormData !== this.formData;
      },
      this.hasEditsValue ? longDuration : shortDuration,
    );

    return this.runningCheck();
  }

  /**
   * Clear the tracking changes values and messages.
   */
  clear() {
    this.hasCommentsValue = false;
    this.hasEditsValue = false;
  }

  /**
   * Trigger the beforeunload confirmation dialog if active (confirm value exists).
   * @see https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event
   */
  confirm(event: BeforeUnloadEvent) {
    const confirmationMessage = this.confirmationValue;

    if (!confirmationMessage) return null;

    if (this.forceValue || this.hasCommentsValue || this.hasEditsValue) {
      // eslint-disable-next-line no-param-reassign
      event.returnValue = confirmationMessage;

      return confirmationMessage;
    }

    return null;
  }

  hasCommentsValueChanged(current: boolean, previous: boolean) {
    if (current !== previous) this.notify();
  }

  hasEditsValueChanged(current: boolean, previous: boolean) {
    if (current !== previous) this.notify();
  }

  /**
   * Notify the user of changes to the form.
   * Dispatch events to update the footer message via dispatching events.
   */
  notify() {
    const comments = this.hasCommentsValue;
    const edits = this.hasEditsValue;

    if (!comments && !edits) {
      this.dispatch('clear', { cancelable: false });
      return;
    }

    const [type] = [
      edits && comments && 'all',
      comments && 'comments',
      edits && 'edits',
    ].filter(Boolean);

    this.dispatch('add', { cancelable: false, detail: { type } });
  }

  /**
   * When the form is submitted, ensure that the exit confirmation
   * does not trigger. Deactivate the confirmation by setting the
   * confirm value to empty.
   */
  submit() {
    this.confirmationValue = '';
  }

  /**
   * Watch for comment changes, updating the timeout to match the timings for
   * responding to page form changes.
   */
  watchComments({ long: longDuration, short: shortDuration }) {
    let updateIsCommentsDirty;

    const { commentApp } = window.comments;

    const initialComments = commentApp.selectors.selectIsDirty(
      commentApp.store.getState(),
    );

    this.dispatch('watch-edits', {
      cancelable: false,
      detail: { initialComments },
    });

    this.hasCommentsValue = initialComments;

    commentApp.store.subscribe(() => {
      if (updateIsCommentsDirty) {
        updateIsCommentsDirty.cancel();
      }

      updateIsCommentsDirty = debounce(
        () => {
          this.hasCommentsValue = commentApp.selectors.selectIsDirty(
            commentApp.store.getState(),
          );
        },
        this.hasCommentsValue ? longDuration : shortDuration,
      );

      updateIsCommentsDirty();
    });
  }

  /**
   * Delay snap-shotting the form’s data to avoid race conditions with form widgets that might process the values.
   * User interaction with the form within that delay also won’t trigger the confirmation message if
   * they are only quickly viewing the form.
   *
   * While the `check` method will be triggered based on Stimulus actions (e.g. change/keyup) we also
   * want to account for input DOM notes entering/existing the UI and check when that happens.
   */
  watchEdits({ initial: initialDelay }) {
    const form = this.element;

    debounce(() => {
      const initialFormData = this.formData;

      this.initialFormData = initialFormData;

      this.dispatch('watch-edits', {
        cancelable: false,
        detail: { initialFormData },
      });

      const isValidInputNode = (node) =>
        node.nodeType === node.ELEMENT_NODE &&
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(node.tagName);

      const observer = new MutationObserver((mutationList) => {
        const hasMutationWithValidInputNode = mutationList.some(
          (mutation) =>
            Array.from(mutation.addedNodes).some(isValidInputNode) ||
            Array.from(mutation.removedNodes).some(isValidInputNode),
        );

        if (hasMutationWithValidInputNode) this.check();
      });

      observer.observe(form, {
        attributes: false,
        childList: true,
        subtree: true,
      });

      this.observer = observer;
    }, initialDelay)();
  }

  disconnect() {
    if (this.runningCheck) {
      this.runningCheck.cancel();
    }
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  /**
   * Ensure we have backwards compatibility for any window global calls to
   * `window.enableDirtyFormCheck`.
   *
   * @deprecated RemovedInWagtail70
   */
  static afterLoad(identifier: string) {
    /**
     * Support a basic form of the legacy "dirty form check" global initialisation function.
     *
     * @param {string} formSelector - A CSS selector to select the form to apply this check to.
     * @param {Object} options
     * @param {boolean} options.alwaysDirty - When set to true the form will always be considered dirty
     * @param {string} options.confirmationMessage - The message to display in the prompt.
     *
     * @deprecated RemovedInWagtail70
     */
    const enableDirtyFormCheck = (
      formSelector: string,
      { alwaysDirty = false, confirmationMessage = '' },
    ) => {
      domReady().then(() => {
        const form = document.querySelector(
          `${formSelector}:not([data-controller~='${identifier}'])`,
        );

        if (!(form instanceof HTMLFormElement)) return;

        [
          ['data-w-unsaved-confirmation-value', confirmationMessage || ' '],
          ['data-w-unsaved-force-value', String(alwaysDirty || false)],
          ['data-w-unsaved-watch-value', 'edits comments'],
        ].forEach(([key, value]) => {
          form.setAttribute(key, value);
        });

        form.setAttribute(
          'data-action',
          [
            form.getAttribute('data-action') || '',
            'w-unsaved#submit',
            'beforeunload@window->w-unsaved#confirm',
            'change->w-unsaved#check',
            'keyup->w-unsaved#check',
          ]
            .filter(Boolean)
            .join(' '),
        );

        form.setAttribute(
          'data-controller',
          [form.getAttribute('data-controller') || '', identifier]
            .filter(Boolean)
            .join(' '),
        );
      });
    };

    window.enableDirtyFormCheck = enableDirtyFormCheck;
  }
}
