import { Controller } from '@hotwired/stimulus';
import { DialogController } from './DialogController';

export class SessionController extends Controller<HTMLElement> {
  static values = {
    interval: { type: Number, default: 1000 * 10 },
  };

  static outlets = [
    // For the confirmation dialog to overwrite changes made by another user.
    'w-dialog',
  ];

  declare readonly intervalValue: number;
  declare readonly hasWDialogOutlet: boolean;
  declare readonly wDialogOutlet: DialogController;
  declare interval: number;
  lastActionButton?: HTMLButtonElement;
  preventSubmit = true;

  connect(): void {
    this.interval = window.setInterval(
      () => this.dispatch('ping'),
      this.intervalValue,
    );

    this.showOverwriteDialog = this.showOverwriteDialog.bind(this);
    this.confirmOverwrite = this.confirmOverwrite.bind(this);
  }

  disconnect(): void {
    window.clearInterval(this.interval);
  }

  dispatchVisibilityState(): void {
    this.dispatch(document.visibilityState);
  }

  showOverwriteDialog(event: Event): void {
    // Store the last action button that triggered the event, so we can
    // trigger it again after the user confirms the overwrite.
    this.lastActionButton = event.target as HTMLButtonElement;

    // Allow us to proceed with the original behaviour (i.e. form submission or
    // workflow action modal) after the user confirms the overwrite.
    if (!this.preventSubmit) return;

    // Prevent form submission
    event.preventDefault();
    // Prevent triggering other event listeners e.g. workflow actions modal
    event.stopImmediatePropagation();

    if (this.wDialogOutlet.hasConfirmTarget) {
      this.wDialogOutlet.confirmTarget.innerText =
        this.lastActionButton.innerText;
    }
    this.wDialogOutlet.show();
  }

  confirmOverwrite(): void {
    if (!this.lastActionButton) return;
    this.preventSubmit = false;
    this.lastActionButton?.click();
    this.preventSubmit = true;
  }

  get submitButtons(): NodeListOf<HTMLButtonElement> {
    return document.querySelectorAll<HTMLButtonElement>(
      '[data-edit-form] button:is([type="submit"], [data-workflow-action-name])',
    );
  }

  wDialogOutletConnected(): void {
    this.submitButtons.forEach((button) => {
      button.addEventListener('click', this.showOverwriteDialog, {
        capture: true,
      });
    });

    this.wDialogOutlet.element.addEventListener(
      'w-dialog:confirmed',
      this.confirmOverwrite,
    );
  }

  wDialogOutletDisconnected(): void {
    this.submitButtons.forEach((button) => {
      button.removeEventListener('click', this.showOverwriteDialog, {
        capture: true,
      });
    });

    this.wDialogOutlet.element.removeEventListener(
      'w-dialog:confirmed',
      this.confirmOverwrite,
    );
  }
}
