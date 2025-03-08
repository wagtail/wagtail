import { Controller } from '@hotwired/stimulus';
import A11yDialog from 'a11y-dialog';

const FLOATING = 'floating';

/**
 * Instantiates an a11y dialog on the controlled element.
 * Adds support for hide and show methods and blocking body
 * scroll when the dialog is open.
 *
 * @example
 * ```html
 * <div
 *   data-controller="w-dialog"
 *   data-w-dialog-theme-value="floating"
 *   >
 *    <div data-w-dialog-target="body"></div>
 * </div>
 * ```
 */
export class DialogController extends Controller<HTMLElement> {
  static values = {
    theme: { default: '', type: String },
  };

  static targets = ['body', 'notify', 'confirm'];

  declare dialog: A11yDialog;
  declare readonly bodyTarget: HTMLElement;
  declare readonly themeValue: string;
  /** Optional targets that will be dispatched events for key dialog events. */
  declare readonly notifyTargets: HTMLElement[];
  declare readonly hasConfirmTarget: boolean;
  declare readonly confirmTarget: HTMLButtonElement;

  get eventDetail() {
    return { body: this.bodyTarget, dialog: this.dialog };
  }

  connect() {
    this.dialog = new A11yDialog(this.element);
    const isFloating = this.themeValue === FLOATING;
    this.dialog
      .on('show', () => {
        if (!isFloating) document.documentElement.style.overflowY = 'hidden';
        this.dispatch('shown', { detail: this.eventDetail, cancelable: false });
        this.notifyTargets.forEach((target) => {
          this.dispatch('shown', {
            target,
            bubbles: false,
            cancelable: false,
          });
        });
      })
      .on('hide', () => {
        if (!isFloating) document.documentElement.style.overflowY = '';
        this.dispatch('hidden', {
          detail: this.eventDetail,
          cancelable: false,
        });
        this.notifyTargets.forEach((target) => {
          this.dispatch('hidden', {
            target,
            bubbles: false,
            cancelable: false,
          });
        });
      });
    this.dispatch('ready', { detail: this.eventDetail });
    if (this.notifyTargets && Array.isArray(this.notifyTargets)) {
      this.notifyTargets.forEach((target) => {
        this.dispatch('ready', { target, bubbles: false, cancelable: false });
      });
    }
    return this.dialog;
  }

  hide() {
    this.dialog.hide();
  }

  show() {
    this.dialog.show();
  }

  confirm() {
    this.hide();
    this.dispatch('confirmed', { detail: this.eventDetail, cancelable: false });
  }
}
