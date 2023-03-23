import axe from 'axe-core';

import { Controller } from '@hotwired/stimulus';
import type { ContextObject } from 'axe-core';
import {
  getAxeConfiguration,
  getA11yReport,
  renderA11yResults,
} from '../includes/a11y-result';
import { wagtailPreviewPlugin } from '../includes/previewPlugin';
import {
  getPreviewContentMetrics,
  renderContentMetrics,
} from '../includes/contentMetrics';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { debounce } from '../utils/debounce';
import { gettext } from '../utils/gettext';
import type { ProgressController } from './ProgressController';

const runContentChecks = async () => {
  axe.registerPlugin(wagtailPreviewPlugin);

  const contentMetrics = await getPreviewContentMetrics({
    targetElement: 'main, [role="main"], body',
  });

  renderContentMetrics({
    wordCount: contentMetrics.wordCount,
    readingTime: contentMetrics.readingTime,
  });
};

const runAccessibilityChecks = async (
  onClickSelector: (selectorName: string, event: MouseEvent) => void,
) => {
  const a11yRowTemplate = document.querySelector<HTMLTemplateElement>(
    '#w-a11y-result-row-template',
  );
  const checksPanel = document.querySelector<HTMLElement>(
    '[data-checks-panel]',
  );
  const config = getAxeConfiguration(document.body);
  const toggleCounter = document.querySelector<HTMLElement>(
    '[data-side-panel-toggle="checks"] [data-side-panel-toggle-counter]',
  );
  const panelCounter = document.querySelector<HTMLElement>(
    '[data-side-panel="checks"] [data-a11y-result-count]',
  );

  if (
    !checksPanel ||
    !a11yRowTemplate ||
    !config ||
    !toggleCounter ||
    !panelCounter
  ) {
    return;
  }

  // Ensure we only test within the preview iframe, but nonetheless with the correct selectors.
  config.context = {
    include: {
      fromFrames: ['#w-preview-iframe'].concat(
        (config.context as ContextObject).include as string[],
      ),
    },
  } as ContextObject;
  if ((config.context.exclude as string[])?.length > 0) {
    config.context.exclude = {
      fromFrames: ['#w-preview-iframe'].concat(
        config.context.exclude as string[],
      ),
    } as ContextObject['exclude'];
  }

  const { results, a11yErrorsNumber } = await getA11yReport(config);

  toggleCounter.innerText = a11yErrorsNumber.toString();
  toggleCounter.hidden = a11yErrorsNumber === 0;
  panelCounter.innerText = a11yErrorsNumber.toString();
  panelCounter.classList.toggle('has-errors', a11yErrorsNumber > 0);

  renderA11yResults(
    checksPanel,
    results,
    config,
    a11yRowTemplate,
    onClickSelector,
  );
};

/**
 * Controls the preview panel component to submit the current form state and
 * update the preview iframe if the form is valid.
 */
export class PreviewController extends Controller<HTMLElement> {
  static classes = ['hasErrors', 'selectedSize'];

  static targets = ['size', 'newTab', 'spinner', 'mode', 'iframe'];

  static values = {
    url: { default: '', type: String },
    autoUpdate: { default: true, type: Boolean },
    autoUpdateInterval: { default: 500, type: Number },
    deviceWidthProperty: { default: '--preview-device-width', type: String },
    panelWidthProperty: { default: '--preview-panel-width', type: String },
    deviceLocalStorageKey: {
      default: 'wagtail:preview-panel-device',
      type: String,
    },
  };

  static outlets = ['w-progress'];

  declare readonly hasErrorsClass: string;
  declare readonly selectedSizeClass: string;

  declare readonly sizeTargets: HTMLInputElement[];
  declare readonly hasNewTabTarget: boolean;
  declare readonly newTabTarget: HTMLAnchorElement;
  declare readonly hasSpinnerTarget: boolean;
  declare readonly spinnerTarget: HTMLDivElement;
  declare readonly hasModeTarget: boolean;
  declare readonly modeTarget: HTMLSelectElement;
  declare readonly iframeTarget: HTMLIFrameElement;
  declare readonly iframeTargets: HTMLIFrameElement[];
  declare readonly urlValue: string;
  declare readonly autoUpdateValue: boolean;
  declare readonly autoUpdateIntervalValue: number;
  declare readonly deviceWidthPropertyValue: string;
  declare readonly panelWidthPropertyValue: string;
  declare readonly deviceLocalStorageKeyValue: string;

  declare readonly hasWProgressOutlet: boolean;
  declare readonly wProgressOutlet: ProgressController;

  // Instance variables with initial values set in connect()
  declare editForm: HTMLFormElement;
  declare sidePanelContainer: HTMLDivElement;
  declare checksSidePanel: HTMLDivElement | null;
  declare resizeObserver: ResizeObserver;

  // Instance variables with initial values set here
  spinnerTimeout: ReturnType<typeof setTimeout> | null = null;
  updateInterval: ReturnType<typeof setInterval> | null = null;
  cleared = false;
  available = true;
  updatePromise: Promise<boolean> | null = null;
  formPayload = '';

  /**
   * The default size input element.
   * This is the size input element with the `data-default-size` data attribute.
   * If no input element has this attribute, the first size input element will be used.
   */
  get defaultSizeInput(): HTMLInputElement {
    return (
      this.sizeTargets.find((input) => 'defaultSize' in input.dataset) ||
      this.sizeTargets[0]
    );
  }

  /**
   * The currently active device size input element. Falls back to the default size input.
   */
  get activeSizeInput(): HTMLInputElement {
    return (
      this.sizeTargets.find((input) => input.checked) || this.defaultSizeInput
    );
  }

  /**
   * Sets the simulated device width of the preview iframe.
   * @param width The width of the preview device. If falsy:
   * - the default size will be used if the preview is currently unavailable,
   * - otherwise, the currently selected device size is used.
   */
  setPreviewWidth(width?: string) {
    let deviceWidth = width;
    if (!width) {
      // Restore width using the currently active device size input
      deviceWidth = this.activeSizeInput.dataset.deviceWidth;
    }

    if (!this.available) {
      // Ensure the 'Preview not available' message is not scaled down
      deviceWidth = this.defaultSizeInput.dataset.deviceWidth;
    }

    this.element.style.setProperty(
      this.deviceWidthPropertyValue,
      deviceWidth as string,
    );
  }

  /**
   * Toggles the preview size based on the selected input.
   * The selected device name (`input[value]`) is stored in localStorage.
   * @param event `InputEvent` from the size input
   */
  togglePreviewSize(event: InputEvent) {
    const target = event.target as HTMLInputElement;
    const device = target.value;
    const deviceWidth = target.dataset.deviceWidth;

    this.setPreviewWidth(deviceWidth);
    try {
      localStorage.setItem(this.deviceLocalStorageKeyValue, device);
    } catch (e) {
      // Skip saving the device if localStorage fails.
    }

    // Ensure only one selected class is applied
    this.sizeTargets.forEach((input) => {
      // The <input> is invisible and we're using a <label> parent to style it.
      input.labels?.forEach((label) =>
        label.classList.toggle(this.selectedSizeClass, input.value === device),
      );
    });
  }

  /**
   * Observes the preview panel size and set the `--preview-panel-width` CSS variable.
   * This is used to maintain the simulated device width as the side panel is resized.
   */
  observePanelSize() {
    const resizeObserver = new ResizeObserver((entries) =>
      this.element.style.setProperty(
        this.panelWidthPropertyValue,
        entries[0].contentRect.width.toString(),
      ),
    );
    resizeObserver.observe(this.element);
    return resizeObserver;
  }

  /**
   * Resets the preview panel state to be ready for the next update.
   */
  finishUpdate() {
    if (this.spinnerTimeout) {
      clearTimeout(this.spinnerTimeout);
      this.spinnerTimeout = null;
    }
    if (this.hasSpinnerTarget) {
      this.spinnerTarget.hidden = true;
    }
    if (this.hasWProgressOutlet) {
      this.wProgressOutlet.loadingValue = false;
    }
    if (!this.cleared) {
      this.cleared = true;
    }
    this.updatePromise = null;

    // Ensure the width is set to the default size if the preview is unavailable,
    // or the currently selected device size if the preview is available.
    this.setPreviewWidth();
  }

  /**
   * Reloads the preview iframe.
   *
   * Instead of reloading the iframe with `iframe.contentWindow.location.reload()`
   * or updating the `src` attribute, this works by creating a new iframe that
   * replaces the old one once the new one has been loaded. This prevents the
   * iframe from flashing when reloading.
   */
  reloadIframe() {
    // Copy the iframe element
    const newIframe = this.iframeTarget.cloneNode() as HTMLIFrameElement;

    // The iframe does not have an src attribute on initial load,
    // so we need to set it here. For subsequent loads, it's fine to set it
    // again to ensure it's in sync with the selected preview mode.
    const url = new URL(this.urlValue, window.location.href);
    if (this.hasModeTarget) {
      url.searchParams.set('mode', this.modeTarget.value);
    }
    url.searchParams.set('in_preview_panel', 'true');
    newIframe.src = url.toString();

    // Make the new iframe invisible
    newIframe.style.width = '0';
    newIframe.style.height = '0';
    newIframe.style.opacity = '0';
    newIframe.style.position = 'absolute';

    // Put it in the DOM so it loads the page
    this.iframeTarget.insertAdjacentElement('afterend', newIframe);
  }

  /**
   * Replaces the old iframe with the new iframe.
   * @param event The `load` event from the new iframe
   */
  replaceIframe(event: Event) {
    const newIframe = event.target as HTMLIFrameElement;

    // Restore scroll position
    newIframe.contentWindow?.scroll(
      this.iframeTarget.contentWindow?.scrollX as number,
      this.iframeTarget.contentWindow?.scrollY as number,
    );

    // Remove the old iframe
    // This will disconnect the old iframe target, but it's fine because
    // the new iframe has been connected when we copy the attributes over,
    // thus subsequent references to this.iframeTarget will be the new iframe.
    // To verify, you can add console.log(this.iframeTargets) before and after
    // the following line and see that the array contains two and then one iframe.
    this.iframeTarget.remove();

    // Make the new iframe visible
    newIframe.removeAttribute('style');

    runContentChecks();

    const onClickSelector = () => this.newTabTarget.click();
    runAccessibilityChecks(onClickSelector);

    // Ready for another update
    this.finishUpdate();
  }

  /**
   * Clears the preview data from the session.
   * @returns `Response` from the fetch `DELETE` request
   */
  async clearPreviewData() {
    return fetch(this.urlValue, {
      headers: {
        [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      },
      method: 'DELETE',
    }).then((response) => {
      this.available = false;
      this.reloadIframe();
      return response;
    });
  }

  /**
   * Updates the preview data in the session. If the data is valid, the preview
   * iframe will be reloaded. If the data is invalid, the preview panel will
   * display an error message.
   * @returns whether the data is valid
   */
  async setPreviewData() {
    // Bail out if there is already a pending update
    if (this.updatePromise) return this.updatePromise;

    // Store the promise so that subsequent calls to setPreviewData will
    // return the same promise as long as it hasn't finished yet
    this.updatePromise = (async () => {
      if (this.hasSpinnerTarget) {
        this.spinnerTimeout = setTimeout(() => {
          this.spinnerTarget.hidden = false;
        }, 2000);
      }

      try {
        const response = await fetch(this.urlValue, {
          method: 'POST',
          body: new FormData(this.editForm),
        });
        const data = await response.json();

        this.element.classList.toggle(this.hasErrorsClass, !data.is_valid);
        this.available = data.is_available;

        if (data.is_valid) {
          this.reloadIframe();
        } else if (!this.cleared) {
          this.updatePromise = this.clearPreviewData().then(() => false);
        } else {
          // Finish the process when the data is invalid to prepare for the next update
          // and avoid elements like the loading spinner to be shown indefinitely
          this.finishUpdate();
        }

        return data.is_valid as boolean;
      } catch (error) {
        this.finishUpdate();
        // Re-throw error so it can be handled by setPreviewDataWithAlert
        throw error;
      }
    })();

    return this.updatePromise;
  }

  /**
   * Like `setPreviewData`, but only updates the preview if there is no pending
   * update and the form has not changed.
   * @returns whether the data is valid
   */
  async checkAndUpdatePreview() {
    // Small performance optimisation: the hasChanges() method will not be called
    // if there is a pending update due to the || operator short-circuiting
    if (this.updatePromise || !this.hasChanges()) return undefined;
    return this.setPreviewData();
  }

  /**
   * Like `setPreviewData`, but also displays an alert if an error occurred while
   * updating the preview data. Note that this will not display an alert if the
   * update request was successful, but the data is invalid.
   *
   * This is useful when the preview data is updated in response to a user
   * interaction, such as:
   * - clicking the "open in new tab" link
   * - clicking the "Refresh" button (if auto update is disabled)
   * - changing the preview mode.
   * @returns whether the data is valid
   */
  async setPreviewDataWithAlert() {
    try {
      return await this.setPreviewData();
    } catch {
      // eslint-disable-next-line no-alert
      window.alert(gettext('Error while sending preview data.'));
      // we don't know if the data is valid or not as the request failed
      return undefined;
    }
  }

  /**
   * Like `setPreviewDataWithAlert`, but also opens the preview in a new tab.
   * If an existing tab for the preview is already open, it will be focused and
   * reloaded.
   * @param event The click event
   * @returns whether the data is valid
   */
  async openPreviewInNewTab(event: MouseEvent) {
    event.preventDefault();
    const link = event.currentTarget as HTMLAnchorElement;

    const valid = await this.setPreviewDataWithAlert();

    // Use the base URL value (without any params) as the target (identifier)
    // for the window, so that if the user switches between preview modes,
    // the same window will be reused.
    window.open(new URL(link.href).toString(), this.urlValue) as Window;

    return valid;
  }

  /**
   * Checks whether the form data has changed since the last call to this method.
   * @returns whether the form data has changed
   */
  hasChanges() {
    // https://github.com/microsoft/TypeScript/issues/30584
    const newPayload = new URLSearchParams(
      new FormData(this.editForm) as unknown as Record<string, string>,
    ).toString();
    const changed = this.formPayload !== newPayload;

    this.formPayload = newPayload;
    return changed;
  }

  /**
   * Activates the preview mechanism.
   * The preview data is immediately updated. If auto-update is enabled,
   * debounce is applied to setPreviewData for subsequent calls, and an interval
   * is set up to automatically check the form and update the preview data.
   */
  activatePreview() {
    // Immediately update the preview when the panel is opened
    this.checkAndUpdatePreview();

    // Skip setting up the interval if auto update is disabled
    if (!this.autoUpdateValue) return;

    // Apply debounce for subsequent updates if not already applied
    if (!('cancel' in this.setPreviewData)) {
      this.setPreviewData = debounce(
        this.setPreviewData.bind(this),
        this.autoUpdateIntervalValue,
      );
    }

    // Only set the interval while the panel is shown
    // This interval performs the checks for changes but not necessarily the
    // update itself
    if (!this.updateInterval) {
      this.updateInterval = setInterval(
        this.checkAndUpdatePreview.bind(this),
        this.autoUpdateIntervalValue,
      );
    }
  }

  /**
   * Deactivates the preview mechanism.
   *
   * If auto-update is enabled, clear the auto-update interval.
   */
  deactivatePreview() {
    if (!this.updateInterval) return;
    clearInterval(this.updateInterval);
    this.updateInterval = null;
  }

  /**
   * Sets the preview mode in the iframe and new tab URLs,
   * then updates the preview.
   * @param event Event from the `<select>` element
   */
  setPreviewMode(event: Event) {
    const mode = (event.target as HTMLSelectElement).value;
    const url = new URL(this.urlValue, window.location.href);

    // Update the new tab link
    url.searchParams.set('mode', mode);
    this.newTabTarget.href = url.toString();

    // Make sure data is updated and an alert is displayed if an error occurs
    this.setPreviewDataWithAlert();
  }

  connect() {
    if (!this.urlValue) {
      throw new Error(
        `The preview panel controller requires the data-${this.identifier}-url-value attribute to be set`,
      );
    }

    this.resizeObserver = this.observePanelSize();

    this.editForm = document.querySelector<HTMLFormElement>(
      '[data-edit-form]',
    ) as HTMLFormElement;

    // This controller is encapsulated as a child of the side panel element,
    // so we need to listen to the show/hide events on the parent element
    // (the one with [data-side-panel]).
    // If we had support for data-controller attribute on the side panels,
    // we could remove the intermediary element and make the [data-side-panel]
    // element to also act as the controller.
    this.sidePanelContainer = this.element.parentElement as HTMLDivElement;

    this.checksSidePanel = document.querySelector('[data-side-panel="checks"]');

    this.activatePreview = this.activatePreview.bind(this);
    this.deactivatePreview = this.deactivatePreview.bind(this);

    this.sidePanelContainer.addEventListener('show', this.activatePreview);
    this.sidePanelContainer.addEventListener('hide', this.deactivatePreview);

    this.checksSidePanel?.addEventListener('show', this.activatePreview);
    this.checksSidePanel?.addEventListener('hide', this.deactivatePreview);

    this.restoreLastSavedPreferences();
  }

  disconnect(): void {
    this.sidePanelContainer.removeEventListener('show', this.activatePreview);
    this.sidePanelContainer.removeEventListener('hide', this.deactivatePreview);

    this.checksSidePanel?.removeEventListener('show', this.activatePreview);
    this.checksSidePanel?.removeEventListener('hide', this.deactivatePreview);

    this.resizeObserver.disconnect();
  }

  /**
   * Restores the last saved preferences.
   * Currently, only the last selected device size is restored.
   */
  restoreLastSavedPreferences() {
    // Remember last selected device size
    let lastDevice: string | null = null;
    try {
      lastDevice = localStorage.getItem(this.deviceLocalStorageKeyValue);
    } catch (e) {
      // Initialise with the default device if the last one cannot be restored.
    }
    const lastDeviceInput =
      this.sizeTargets.find((input) => input.value === lastDevice) ||
      this.defaultSizeInput;
    lastDeviceInput.click();
  }
}
