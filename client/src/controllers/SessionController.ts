import { Controller } from '@hotwired/stimulus';
import { DialogController } from './DialogController';

/**
 * Manage an editing session by indicating the presence of the user and handling
 * cases when there are multiple users editing the same content.
 *
 * This controller defines the following behaviors:
 * - Dispatching a ping event periodically, which can be utilized by other
 *   controllers to keep the session alive or indicate presence.
 * - Dispatching an event indicating the visibility state of the document.
 * - Preventing events triggered by submit buttons and workflow action buttons
 *   in the edit form, and showing a confirmation dialog instead, before
 *   proceeding with the original action after the user confirms the dialog.
 *
 * Ideally this controller should be used in conjunction with `SwapController`,
 * `ActionController`, and `DialogController` to compose the user experience.
 *
 * @example
 * ```html
 * <form
 *   id="w-editing-sessions"
 *   method="post"
 *   data-controller="w-swap w-action w-session"
 *   data-w-swap-target-value="#w-editing-sessions"
 *   data-w-swap-src-value="/path/to/ping/session/"
 *   data-w-swap-json-path-value="html"
 *   data-w-action-continue-value="true"
 *   data-w-action-url-value="/path/to/release/session/"
 *   data-w-session-w-dialog-outlet="[data-edit-form] [data-controller='w-dialog']#w-overwrite-changes-dialog"
 *   data-action="visibilitychange@document->w-session#dispatchVisibilityState w-session:visible->w-session#ping w-session:visible->w-session#addInterval w-session:hidden->w-session#clearInterval w-session:hidden->w-action#sendBeacon"
 * >
 * </form>
 * ```
 */
export class SessionController extends Controller<HTMLElement> {
  static values = {
    interval: { type: Number, default: 1000 * 10 }, // 10 seconds
    intercept: { type: Boolean, default: true },
  };

  static outlets = ['w-dialog'];

  declare readonly hasWDialogOutlet: boolean;
  /** The confirmation dialog for overwriting changes made by another user */
  declare readonly wDialogOutlet: DialogController;
  /** The interval duration for the ping event */
  declare intervalValue: number;
  /** Whether to intercept the original event and show a confirmation dialog */
  declare interceptValue: boolean;

  /** The interval ID for the periodic pinging */
  declare interval: number;
  /** The last action button that triggered the event */
  lastActionButton?: HTMLButtonElement;

  initialize(): void {
    // Bind these methods in initialize() instead of connect, as they will be
    // used as event listeners for other controllers e.g. DialogController, and
    // they may be connected before this controller is connected.
    this.showConfirmationDialog = this.showConfirmationDialog.bind(this);
    this.confirmAction = this.confirmAction.bind(this);
    this.ping = this.ping.bind(this);
  }

  connect(): void {
    this.interceptTargets.forEach((button) => {
      // Match the event listener configuration of workflow-action that uses
      // capture so we can intercept the workflow-action's listener.
      button.addEventListener('click', this.showConfirmationDialog, {
        capture: true,
      });
    });

    // Do a ping so the sessions list can be loaded immediately.
    this.ping();
  }

  /**
   * Buttons that will be intercepted to show the confirmation dialog.
   *
   * Defaults to submit buttons and workflow action buttons in the edit form.
   */
  get interceptTargets(): NodeListOf<HTMLButtonElement> {
    return document?.querySelectorAll<HTMLButtonElement>(
      '[data-edit-form] button:is([type="submit"], [data-workflow-action-name])',
    );
  }

  /**
   * Dispatch a ping event, to be used by other controllers to keep the session
   * alive or indicate presence.
   */
  ping(): void {
    this.dispatch('ping');
  }

  intervalValueChanged(): void {
    this.addInterval();
  }

  /**
   * Set the interval for the periodic pinging, clearing the previous interval
   * if it exists.
   */
  addInterval(): void {
    this.clearInterval();
    this.interval = window.setInterval(this.ping, this.intervalValue);
  }

  /**
   * Clear the interval for the periodic pinging if one is set.
   */
  clearInterval(): void {
    if (this.interval) {
      window.clearInterval(this.interval);
    }
  }

  /**
   * Dispatch the visibility state of the document. When used as an event
   * listener for the `visibilitychange` event, it will dispatch two separate
   * events: `identifier:visible` and `identifier:hidden`, which makes it easier
   * to attach event listeners to specific visibility states.
   */
  dispatchVisibilityState(): void {
    this.dispatch(document.visibilityState);
  }

  /**
   * Intercept the original event and show a confirmation dialog instead.
   *
   * The interception can be controlled dynamically via the `interceptValue`
   * so that we can temporarily disable it when the user confirms the overwrite
   * and immediately reenable it without having to remove and re-add the event
   * listener. This is useful for events that are triggered by a multi-step
   * process, such as a workflow action, which may have its own dialogs and may
   * be cancelled in the middle of the process.
   *
   * @param event The original event that triggered the action.
   */
  showConfirmationDialog(event: Event): void {
    // Store the last action button that triggered the event, so we can
    // trigger it again after the user confirms the dialog.
    this.lastActionButton = event.target as HTMLButtonElement;

    // Allow us to proceed with the original behaviour (i.e. form submission or
    // workflow action modal) after the user confirms the dialog.
    if (!this.interceptValue || !this.hasWDialogOutlet) return;

    // Prevent form submission
    event.preventDefault();
    // Prevent triggering other event listeners e.g. workflow actions modal
    event.stopImmediatePropagation();

    if (this.wDialogOutlet.hasConfirmTarget && this.lastActionButton) {
      this.wDialogOutlet.confirmTarget.textContent =
        this.lastActionButton.textContent;
    }
    this.wDialogOutlet.show();
  }

  /**
   * Proceed with the original action after the user confirms the dialog.
   */
  confirmAction(): void {
    this.interceptValue = false;
    this.lastActionButton?.click();
    this.interceptValue = true;
  }

  wDialogOutletConnected(): void {
    this.wDialogOutlet.element.addEventListener(
      'w-dialog:confirmed',
      this.confirmAction,
    );
  }

  disconnect(): void {
    if (this.interval) {
      window.clearInterval(this.interval);
    }
    this.interceptTargets?.forEach((button) => {
      button.removeEventListener('click', this.showConfirmationDialog, {
        capture: true,
      });
    });
  }
}
