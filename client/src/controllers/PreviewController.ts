import { Controller } from '@hotwired/stimulus';
import type { ContextObject } from 'axe-core';
import {
  getAxeConfiguration,
  getA11yReport,
  renderA11yResults,
} from '../includes/a11y-result';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { debounce } from '../utils/debounce';
import { gettext } from '../utils/gettext';
import type { ProgressController } from './ProgressController';

const runAccessibilityChecks = async (
  onClickSelector: (selectorName: string, event: MouseEvent) => void,
) => {
  const a11yRowTemplate = document.querySelector<HTMLTemplateElement>(
    '#w-a11y-result-row-template',
  );
  const a11ySelectorTemplate = document.querySelector<HTMLTemplateElement>(
    '#w-a11y-result-selector-template',
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
    !a11ySelectorTemplate ||
    !config ||
    !toggleCounter ||
    !panelCounter
  ) {
    return;
  }

  // Ensure we only test within the preview iframe, but nonetheless with the correct selectors.
  config.context = {
    include: {
      fromFrames: ['#preview-iframe'].concat(
        (config.context as ContextObject).include as string[],
      ),
    },
  } as ContextObject;
  if ((config.context.exclude as string[])?.length > 0) {
    config.context.exclude = {
      fromFrames: ['#preview-iframe'].concat(
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
    a11ySelectorTemplate,
    onClickSelector,
  );
};

/**
 * Controls the preview panel component to submit the current form state and
 * update the preview iframe if the form is valid.
 */
export class PreviewController extends Controller<HTMLElement> {
  static classes = ['unavailable', 'hasErrors', 'selectedSize'];

  static targets = ['size', 'newTab', 'spinner', 'mode', 'iframe'];

  static values = {
    url: { default: '', type: String },
    autoUpdate: { default: true, type: Boolean },
    autoUpdateInterval: { default: 500, type: Number },
  };

  static outlets = ['w-progress'];

  declare readonly unavailableClass: string;
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

  declare readonly hasWProgressOutlet: boolean;
  declare readonly wProgressOutlet: ProgressController;

  // Instance variables with initial values set in connect()
  declare editForm: HTMLFormElement;

  // Instance variables with initial values set here
  spinnerTimeout: ReturnType<typeof setTimeout> | null = null;
  cleared = false;
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
   * Sets the simulated device width of the preview iframe.
   * @param width The width of the preview device. If falsy, the default size will be used.
   */
  setPreviewWidth(width?: string) {
    const isUnavailable = this.element.classList.contains(
      this.unavailableClass,
    );

    let deviceWidth = width;
    // Reset to default size if width is falsy or preview is unavailable
    if (!width || isUnavailable) {
      deviceWidth = this.defaultSizeInput.dataset.deviceWidth;
    }

    this.element.style.setProperty(
      '--preview-device-width',
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
      localStorage.setItem('wagtail:preview-panel-device', device);
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
        '--preview-panel-width',
        entries[0].contentRect.width.toString(),
      ),
    );
    resizeObserver.observe(this.element);
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
    this.updatePromise = null;
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

    const handleLoad = () => {
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

      // Ready for another update
      this.finishUpdate();

      // Remove the load event listener so it doesn't fire when switching modes
      newIframe.removeEventListener('load', handleLoad);

      const onClickSelector = () => this.newTabTarget.click();
      runAccessibilityChecks(onClickSelector);
    };

    newIframe.addEventListener('load', handleLoad);
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
        this.element.classList.toggle(
          this.unavailableClass,
          !data.is_available,
        );

        if (!data.is_available) {
          // Ensure the 'Preview not available' message is not scaled down
          this.setPreviewWidth();
        }

        if (data.is_valid) {
          this.reloadIframe();
        } else if (!this.cleared) {
          this.clearPreviewData();
          this.cleared = true;
          this.reloadIframe();
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
   * Initialises the auto update mechanism. This works by comparing the current
   * form data with the previous form data at a set interval. If the form data
   * has changed, the preview will be updated. The interval is only active when
   * the side panel is shown.
   */
  initAutoUpdate() {
    let updateInterval: ReturnType<typeof setInterval>;

    // This controller is encapsulated as a child of the side panel element,
    // so we need to listen to the show/hide events on the parent element
    // (the one with [data-side-panel]).
    // If we had support for data-controller attribute on the side panels,
    // we could remove the intermediary element and make the [data-side-panel]
    // element to also act as the controller.
    const sidePanelContainer = this.element.parentElement as HTMLDivElement;

    const checksSidePanel = document.querySelector(
      '[data-side-panel="checks"]',
    );

    // Apply debounce to the setPreviewData method
    this.setPreviewData = debounce(
      this.setPreviewData.bind(this),
      this.autoUpdateIntervalValue,
    );

    sidePanelContainer.addEventListener('show', () => {
      // Immediately update the preview when the panel is opened
      this.checkAndUpdatePreview();

      // Only set the interval while the panel is shown
      // This interval performs the checks for changes but not necessarily the
      // update itself
      updateInterval = setInterval(
        this.checkAndUpdatePreview.bind(this),
        this.autoUpdateIntervalValue,
      );
    });

    // Use the same processing as the preview panel.
    checksSidePanel?.addEventListener('show', () => {
      this.checkAndUpdatePreview();
      updateInterval = setInterval(
        this.checkAndUpdatePreview.bind(this),
        WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL,
      );
    });

    // Clear the interval when the panel is hidden
    sidePanelContainer.addEventListener('hide', () => {
      clearInterval(updateInterval);
    });
    checksSidePanel?.addEventListener('hide', () => {
      clearInterval(updateInterval);
    });
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
    const checksSidePanel = document.querySelector(
      '[data-side-panel="checks"]',
    );

    if (!this.urlValue) {
      throw new Error(
        `The preview panel controller requires the data-${this.identifier}-base-url-value attribute to be set`,
      );
    }

    this.observePanelSize();

    this.editForm = document.querySelector<HTMLFormElement>(
      '[data-edit-form]',
    ) as HTMLFormElement;

    // This controller is encapsulated as a child of the side panel element,
    // so we need to listen to the show/hide events on the parent element
    // (the one with [data-side-panel]).
    // If we had support for data-controller attribute on the side panels,
    // we could remove the intermediary element and make the [data-side-panel]
    // element to also act as the controller.
    const sidePanelContainer = this.element.parentElement as HTMLDivElement;

    if (this.autoUpdateValue) {
      this.initAutoUpdate();
    } else {
      // Even if the preview is not updated automatically, we still need to
      // initialise the preview data when the panel is shown
      sidePanelContainer.addEventListener('show', () => {
        this.setPreviewData();
      });
      checksSidePanel?.addEventListener('show', () => {
        this.setPreviewData();
      });
    }

    this.restoreLastSavedPreferences();
  }

  /**
   * Restores the last saved preferences.
   * Currently, only the last selected device size is restored.
   */
  restoreLastSavedPreferences() {
    // Remember last selected device size
    let lastDevice: string | null = null;
    try {
      lastDevice = localStorage.getItem('wagtail:preview-panel-device');
    } catch (e) {
      // Initialise with the default device if the last one cannot be restored.
    }
    const lastDeviceInput =
      this.sizeTargets.find((input) => input.value === lastDevice) ||
      this.defaultSizeInput;
    lastDeviceInput.click();
  }
}
