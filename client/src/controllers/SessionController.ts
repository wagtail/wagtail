import { Controller } from '@hotwired/stimulus';
import { DialogController } from './DialogController';
import { SwapController } from './SwapController';
import { ActionController } from './ActionController';
import { setOptionalInterval } from '../utils/interval';

interface PingResponse {
  session_id: string;
  ping_url: string;
  release_url: string;
  other_sessions: {
    session_id: string | null;
    user: string;
    last_seen_at: string;
    is_editing: boolean;
    revision_id: number | null;
  }[];
  html: string;
}

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
    intercept: { type: Boolean, default: false },
  };

  static outlets = ['w-dialog'];

  static targets = ['unsavedChanges', 'reload'];

  declare readonly hasUnsavedChangesTarget: boolean;
  declare readonly hasWDialogOutlet: boolean;
  /** The checkbox input to indicate unsaved changes */
  declare readonly unsavedChangesTarget: HTMLInputElement;
  /** Reload buttons in the sessions' popups */
  declare readonly reloadTargets: HTMLButtonElement[];
  /** The confirmation dialog for overwriting changes made by another user */
  declare readonly wDialogOutlet: DialogController;
  /** The interval duration for the ping event */
  declare intervalValue: number;
  /** Whether to intercept the original event and show a confirmation dialog */
  declare interceptValue: boolean;

  /** The interval ID for the periodic pinging */
  declare interval: number | null;
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
    this.interval = setOptionalInterval(this.ping, this.intervalValue);
  }

  /**
   * Clear the interval for the periodic pinging if one is set.
   */
  clearInterval(): void {
    if (this.interval) {
      window.clearInterval(this.interval);
      this.interval = null;
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
   * and immediately re-enable it without having to remove and re-add the event
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

    // Allow us to proceed with the original behavior (i.e. form submission or
    // workflow action modal) after the user confirms the dialog.
    if (!this.interceptValue || !this.hasWDialogOutlet) return;

    // If the action button is inside a dialog, we need to hide the dialog first
    // so it doesn't interfere with the confirmation dialog
    this.lastActionButton
      ?.closest('[data-controller="w-dialog"]')
      ?.dispatchEvent(new Event('w-dialog:hide'));

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
    // Attach the event listener to the buttons that will be intercepted.
    // Do it here instead of in connect() so hopefully this includes any buttons
    // that are inside a dialog that is connected after this controller
    // (e.g. the schedule publishing dialog).
    this.interceptTargets.forEach((button) => {
      // Match the event listener configuration of workflow-action that uses
      // capture so we can intercept the workflow-action's listener.
      button.addEventListener('click', this.showConfirmationDialog, {
        capture: true,
      });
    });

    this.wDialogOutlet.element.addEventListener(
      'w-dialog:confirmed',
      this.confirmAction,
    );
  }

  wDialogOutletDisconnected(): void {
    this.interceptTargets?.forEach((button) => {
      button.removeEventListener('click', this.showConfirmationDialog, {
        capture: true,
      });
    });
  }

  /**
   * Sets the unsaved changes input state based on the event type dispatched by
   * the w-unsaved controller. If the event type is w-unsaved:add, the input is
   * checked. If the event type is w-unsaved:clear, the input is unchecked.
   *
   * @param event w-unsaved:add or w-unsaved:clear
   * @example - Use via data-action
   * ```html
   * <form
   *   data-controller="w-session"
   *   data-action="w-unsaved:add@document->w-session#setUnsavedChanges w-unsaved:clear@document->w-session#setUnsavedChanges"
   * >
   *   <input type="checkbox" data-w-session-target="unsavedChanges" hidden />
   * </form>
   * ```
   */
  setUnsavedChanges(event: Event) {
    if (!this.hasUnsavedChangesTarget) return;
    const type = event.type.split(':')[1];
    this.unsavedChangesTarget.checked = type !== 'clear';
    this.reloadTargets.forEach((button) => this.reloadTargetConnected(button));
  }

  /**
   * Conditionally set whether the reload button should immediately reload or
   * show the "unsaved changes" dialog based on the unsaved changes state.
   * @param button The reload button to update
   */
  reloadTargetConnected(button: HTMLButtonElement): void {
    if (
      this.hasUnsavedChangesTarget &&
      this.unsavedChangesTarget.checked &&
      button.dataset.dialogId
    ) {
      button.removeAttribute('data-action');
      button.setAttribute('data-a11y-dialog-show', button.dataset.dialogId);
    } else {
      button.removeAttribute('data-a11y-dialog-show');
      button.setAttribute('data-action', 'w-action#reload');
    }
  }

  get swapController() {
    return this.application.getControllerForElementAndIdentifier(
      this.element,
      'w-swap',
    ) as SwapController | null;
  }

  get actionController() {
    return this.application.getControllerForElementAndIdentifier(
      this.element,
      'w-action',
    ) as ActionController | null;
  }

  /**
   * Update the session state with the latest data from the server.
   * @param event an event that contains JSON data in the `detail` property. Normally a `w-swap:json` event.
   */
  updateSessionData(event: CustomEvent) {
    const { detail } = event;
    if (!detail || !detail.data) return;
    const data: PingResponse = detail.data;

    // Update the ping and release URLs in case the session ID has changed
    // e.g. when the user has been inactive for too long and resumed their session.
    // Modify the values via the controllers directly instead of setting the data
    // attributes so we get type checking.
    const swapController = this.swapController;
    if (swapController && data.ping_url) {
      swapController.srcValue = data.ping_url;
    }
    const actionController = this.actionController;
    if (actionController && data.release_url) {
      actionController.urlValue = data.release_url;
    }

    // Set the interceptValue to true if any of the other sessions have a
    // revision ID (assumed to be newer than the one we have loaded)
    if (!data.other_sessions) return;
    this.interceptValue = data.other_sessions.some(
      (session) => session.revision_id,
    );
  }

  disconnect(): void {
    if (this.interval) {
      window.clearInterval(this.interval);
    }
  }
}
