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
import { setOptionalInterval } from '../utils/interval';

const runContentChecks = async () => {
  axe.registerPlugin(wagtailPreviewPlugin);

  const contentMetrics = await getPreviewContentMetrics({
    targetElement: 'main, [role="main"]',
  });

  // This requires Wagtail's preview plugin for axe to be registered in the
  // preview iframe, which is not done in tests as the registration happens via
  // the userbar.
  if (!contentMetrics) return;

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

interface PreviewDataResponse {
  is_valid: boolean;
  is_available: boolean;
}

const PREVIEW_UNAVAILABLE_WIDTH = 375;

/**
 * Controls the preview panel component to submit the current form state and
 * update the preview iframe if the form is valid.
 *
 * Dispatches the following events in this order.
 *
 * @fires PreviewController#update - Before sending the preview data to the server. Cancelable.
 * @fires PreviewController#json - After the preview data update request is completed.
 * @fires PreviewController#error - When an error occurs while updating the preview data.
 * @fires PreviewController#load - Before reloading the preview iframe. Cancelable.
 * @fires PreviewController#loaded - After the preview iframe has been reloaded.
 * @fires PreviewController#ready - When the preview is ready for further updates – only fired on initial load.
 * @fires PreviewController#updated - After an update cycle is finished – may or may not involve reloading the iframe.
 *
 * @event PreviewController#update
 * @type {CustomEvent}
 * @property {boolean} cancelable - Is cancelable
 * @property {string} name - `w-preview:update`
 *
 * @event PreviewController#json
 * @type {CustomEvent}
 * @property {Object} detail
 * @property {PreviewDataResponse} detail.data - The response data that indicates whether the submitted data was valid and whether the preview is available.
 * @property {string} name - `w-preview:json`
 *
 * @event PreviewController#error
 * @type {CustomEvent}
 * @property {Object} detail
 * @property {Error} detail.error - The error object that was thrown.
 * @property {string} name - `w-preview:error`
 *
 * @event PreviewController#load
 * @type {CustomEvent}
 * @property {boolean} cancelable - Is cancelable
 * @property {string} name - `w-preview:load`
 *
 * @event PreviewController#loaded
 * @type {CustomEvent}
 * @property {string} name - `w-preview:loaded`
 *
 * @event PreviewController#ready
 * @type {CustomEvent}
 * @property {string} name - `w-preview:ready`
 *
 * @event PreviewController#updated
 * @type {CustomEvent}
 * @property {string} name - `w-preview:updated`
 */
export class PreviewController extends Controller<HTMLElement> {
  static classes = ['hasErrors', 'proxy', 'selectedSize'];

  static targets = ['iframe', 'mode', 'newTab', 'size', 'spinner'];

  static values = {
    autoUpdateInterval: { default: 500, type: Number },
    deviceLocalStorageKey: {
      default: 'wagtail:preview-panel-device',
      type: String,
    },
    deviceWidthProperty: { default: '--preview-device-width', type: String },
    panelWidthProperty: { default: '--preview-panel-width', type: String },
    renderUrl: { default: '', type: String },
    url: { default: '', type: String },
  };

  static outlets = ['w-progress'];

  /** The device size width to use when the preview is not available. */
  static fallbackWidth = PREVIEW_UNAVAILABLE_WIDTH.toString();

  // Classes

  /** CSS class to indicate that there are errors in the form. */
  declare readonly hasErrorsClass: string;
  /** CSS class for elements that are invisible and only rendered for functionality purposes. */
  declare readonly proxyClass: string;
  /** CSS class for the currently selected device size. */
  declare readonly selectedSizeClass: string;

  // Targets

  /** The main preview `<iframe>` that is currently displayed. */
  declare readonly iframeTarget: HTMLIFrameElement;
  /** All preview `<iframes>` that are currently in the DOM.
   * This contains the currently displayed `<iframe>` and may also contain
   * the new `<iframe>` that will replace the current one. */
  declare readonly iframeTargets: HTMLIFrameElement[];
  /** Preview mode `<select>` element. */
  declare readonly modeTarget: HTMLSelectElement;
  declare readonly hasModeTarget: boolean;
  /** New tab button. */
  declare readonly newTabTarget: HTMLAnchorElement;
  declare readonly hasNewTabTarget: boolean;
  /** Device size `<input type="radio">` elements. */
  declare readonly sizeTargets: HTMLInputElement[];
  /** Loading spinner. */
  declare readonly spinnerTarget: HTMLDivElement;
  declare readonly hasSpinnerTarget: boolean;

  // Values

  /** Interval in milliseconds when the form is checked for changes.
   * Also used as the debounce duration for the update request. */
  declare readonly autoUpdateIntervalValue: number;
  /** Key for storing the last selected device size in localStorage. */
  declare readonly deviceLocalStorageKeyValue: string;
  /** CSS property for setting the device width. */
  declare readonly deviceWidthPropertyValue: string;
  /** CSS property for the current width of the panel, to maintain the device scaling. */
  declare readonly panelWidthPropertyValue: string;
  /** URL for rendering the preview, defaults to `urlValue`.
   * Useful for headless setups where the front-end may be hosted at a different URL. */
  declare renderUrlValue: string;
  /** URL for updating the preview data. Also used for rendering the preview if `renderUrlValue` is unset. */
  declare readonly urlValue: string;

  // Outlets

  /** ProgressController for the refresh button that may be displayed when auto-update is turned off. */
  declare readonly wProgressOutlet: ProgressController;
  declare readonly hasWProgressOutlet: boolean;

  // Instance variables with initial values set in connect()

  /** Side panel for content checks. */
  declare checksSidePanel: HTMLDivElement | null;
  /** Main editor form. */
  declare editForm: HTMLFormElement;
  /** ResizeObserver to observe when the panel is resized
   * so we can maintain the device size scaling. */
  declare resizeObserver: ResizeObserver;
  /** Side panel element of the preview panel, i.e. the element with the
   * `data-side-panel` attribute. Useful for listening to show/hide events.
   * Normally, this is the parent element of the controller element.
   */
  declare sidePanelContainer: HTMLDivElement;

  // Instance variables with initial values set here

  /** Whether the preview is ready for further updates.
   *
   * The preview data is stored in the session, which means:
   * - After logging out and logging back in, the session is cleared, so the
   *   client must send the preview data on initial editor load in order for
   *   Wagtail to render the preview.
   * - The preview data can persist after a full-page reload, as long as they
   *   use the same key in the session.
   *
   * To ensure the preview data is available when the preview panel is opened,
   * we send an update request immediately. This can result in two scenarios:
   *
   * In edit views, the form is usually valid on initial load, as the object was
   * successfully saved before. In this case, we can go ahead with rendering the
   * preview and updating it with any new data.
   *
   * However, there may be cases where the form is invalid on initial load, e.g.
   * if the "expiry date" in the publishing schedule has become in the past.
   * Another common example is in create views, where the form is likely invalid
   * on initial load due to missing required fields (e.g. `title`).
   *
   * When this happens, Wagtail will not update the preview data in the session,
   * which means it may still contain the outdated preview data from the
   * previous full-page load. We want to clear this data immediately so that the
   * preview panel displays the "Preview is not available" screen instead of an
   * outdated preview.
   *
   * This flag determines whether the preview is "ready" for further updates –
   * i.e. this is true if the preview data has been cleared after an invalid
   * initial load, or if the preview data is already valid on initial load.
   *
   * An alternative approach would be to handle the initial state of the
   * session's preview data in the backend, but this would require the logic to
   * be applied in all the different places (i.e. page and snippets create and
   * edit views).
   */
  ready = false;

  /** Whether the preview is currently available. This is used to distinguish
   * whether we are rendering a preview or the "Preview is not available"
   * screen. So even if the preview is currently outdated, this is still `true`
   * as long as the preview data is available and the preview is rendered (e.g.
   * if the form becomes invalid after the preview is successfully rendered).
   */
  available = true;

  /** Serialized form payload to be compared in between intervals to determine
   * whether an update should be performed. Note that we currently do not handle
   * file inputs.
   */
  formPayload = '';

  /** Timeout before displaying the loading spinner. */
  spinnerTimeout: ReturnType<typeof setTimeout> | null = null;

  /** Interval for the auto-update. */
  updateInterval: ReturnType<typeof setOptionalInterval> = null;

  /** Promise for the current update request. This is resolved as soon as the
   * update request is successful, so the preview iframe may not have been
   * fully reloaded.
   */
  updatePromise: Promise<boolean> | null = null;

  /**
   * The currently active device size input element. Falls back to the default size input.
   */
  get activeSizeInput(): HTMLInputElement | null {
    return this.sizeTargets.find((input) => input.checked) || null;
  }

  /**
   * The URL of the preview iframe and the new tab button.
   * This takes into account the currently selected preview mode.
   */
  get renderUrl(): URL {
    const url = new URL(this.renderUrlValue, window.location.href);
    if (this.hasModeTarget) {
      url.searchParams.set('mode', this.modeTarget.value);
    }
    return url;
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
    this.setPreviewData = this.setPreviewData.bind(this);
    this.checkAndUpdatePreview = this.checkAndUpdatePreview.bind(this);

    this.sidePanelContainer.addEventListener('show', this.activatePreview);
    this.sidePanelContainer.addEventListener('hide', this.deactivatePreview);

    this.checksSidePanel?.addEventListener('show', this.activatePreview);
    this.checksSidePanel?.addEventListener('hide', this.deactivatePreview);

    this.restoreLastSavedPreferences();
  }

  renderUrlValueChanged(newValue: string) {
    // Allow the rendering URL to be different from the URL used for sending the
    // preview data (e.g. for a headless setup), but make it optional and use
    // the latter as the default.
    if (!newValue) {
      this.renderUrlValue = this.urlValue;
    }
    this.updateNewTabLink();
  }

  autoUpdateIntervalValueChanged() {
    // If the value is changed, only update the interval if it's currently active
    // as we don't want to start the interval when the panel is hidden
    if (this.updateInterval) this.addInterval();
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
      this.activeSizeInput ||
      this.sizeTargets[0];
    lastDeviceInput.click();
    // If lastDeviceInput resolves to the default input, the click event will
    // not trigger the togglePreviewSize method, so we need to apply the
    // selected size class manually.
    this.applySelectedSizeClass(lastDeviceInput.value);
  }

  /**
   * Activates the preview mechanism.
   * The preview data is immediately updated. If auto-update is enabled,
   * an interval is set up to automatically check the form and update the
   * preview data.
   */
  activatePreview() {
    // Immediately update the preview when the panel is opened
    this.checkAndUpdatePreview();

    // Only set the interval while the panel is shown
    this.addInterval();
  }

  /**
   * Sets the interval for auto-updating the preview and applies debouncing to
   * `setPreviewData` for subsequent calls.
   */
  addInterval() {
    this.clearInterval();
    // This interval performs the checks for changes but not necessarily the
    // update itself
    this.updateInterval = setOptionalInterval(
      this.checkAndUpdatePreview,
      this.autoUpdateIntervalValue,
    );

    if (this.updateInterval) {
      // Apply debounce for subsequent updates if not already applied
      if (!('cancel' in this.setPreviewData)) {
        this.setPreviewData = debounce(
          this.setPreviewData,
          this.autoUpdateIntervalValue,
        );
      }
    }
  }

  /**
   * Clears the auto-update interval.
   */
  clearInterval() {
    if (!this.updateInterval) return;
    window.clearInterval(this.updateInterval);
    this.updateInterval = null;
  }

  /**
   * Deactivates the preview mechanism.
   *
   * If auto-update is enabled, clear the auto-update interval.
   */
  deactivatePreview() {
    this.clearInterval();
  }

  /**
   * Updates the new tab link with the currently selected preview mode,
   * then updates the preview.
   */
  setPreviewMode() {
    this.updateNewTabLink();

    // Make sure data is updated and an alert is displayed if an error occurs
    this.setPreviewDataWithAlert();
  }

  /**
   * Updates the URL of the new tab button with the currently selected preview mode.
   */
  updateNewTabLink() {
    if (this.hasNewTabTarget) {
      this.newTabTarget.href = this.renderUrl.toString();
    }
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
    this.applySelectedSizeClass(device);
    try {
      localStorage.setItem(this.deviceLocalStorageKeyValue, device);
    } catch (e) {
      // Skip saving the device if localStorage fails.
    }
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
      deviceWidth =
        this.activeSizeInput?.dataset.deviceWidth ||
        PreviewController.fallbackWidth;
    }

    if (!this.available) {
      // Ensure the 'Preview not available' message is not scaled down
      deviceWidth = PreviewController.fallbackWidth;
    }

    this.element.style.setProperty(
      this.deviceWidthPropertyValue,
      deviceWidth as string,
    );
  }

  /**
   * Applies the selected size class to the specified device input's label, and
   * removes the class from all other device inputs' labels.
   * @param device Selected device name
   */
  applySelectedSizeClass(device: string) {
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
   * Like `setPreviewData`, but only updates the preview if there is no pending
   * update and the form has not changed.
   * @returns whether the data is valid
   */
  async checkAndUpdatePreview() {
    // Small performance optimization: the hasChanges() method will not be called
    // if there is a pending update due to the || operator short-circuiting
    if (this.updatePromise || !this.hasChanges()) return undefined;
    return this.setPreviewData();
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
   * Updates the preview data in the session. If the data is valid, the preview
   * iframe will be reloaded. If the data is invalid, the preview panel will
   * display an error message.
   * @returns whether the data is valid
   */
  async setPreviewData() {
    // Bail out if there is already a pending update
    if (this.updatePromise) return this.updatePromise;

    const updateEvent = this.dispatch('update');
    if (updateEvent.defaultPrevented) return undefined;

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
        const data: PreviewDataResponse = await response.json();

        this.dispatch('json', { cancelable: false, detail: { data } });

        this.element.classList.toggle(this.hasErrorsClass, !data.is_valid);
        this.available = data.is_available;

        if (data.is_valid) {
          this.reloadIframe();
        } else if (!this.ready) {
          // This is the first update and the form data is not valid.

          // If the preview contains stale valid data from the previous session
          // (hence available), we want to clear it immediately to show the
          // "Preview is not available" screen instead of the outdated preview.
          if (data.is_available) {
            this.updatePromise = this.clearPreviewData().then(() => false);
          } else {
            // There is no stale data, but we still need to load the iframe to
            // show the "Preview is not available" screen, because initially
            // the iframe is empty (to prevent loading the iframe when the panel
            // is never opened).
            this.reloadIframe();
          }
        } else {
          // Finish the process when the data is invalid to prepare for the next update
          // and avoid elements like the loading spinner to be shown indefinitely
          this.finishUpdate();
        }

        return data.is_valid as boolean;
      } catch (error) {
        this.dispatch('error', { cancelable: false, detail: { error } });
        this.finishUpdate();
        // Re-throw error so it can be handled by setPreviewDataWithAlert
        throw error;
      }
    })();

    return this.updatePromise;
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
   * Reloads the preview iframe.
   *
   * Instead of reloading the iframe with `iframe.contentWindow.location.reload()`
   * or updating the `src` attribute, this works by creating a new iframe that
   * replaces the old one once the new one has been loaded. This prevents the
   * iframe from flashing when reloading.
   */
  reloadIframe() {
    const loadEvent = this.dispatch('load');
    if (loadEvent.defaultPrevented) {
      // The load event is cancelled, so don't reload the iframe
      // and immediately finish the update
      this.finishUpdate();
      return;
    }

    // Copy the iframe element
    const newIframe = this.iframeTarget.cloneNode() as HTMLIFrameElement;

    // Remove the ID to avoid duplicate IDs in the DOM
    newIframe.removeAttribute('id');

    // The iframe does not have an src attribute on initial load,
    // so we need to set it here. For subsequent loads, it's fine to set it
    // again to ensure it's in sync with the selected preview mode.
    const url = this.renderUrl;
    url.searchParams.set('in_preview_panel', 'true');
    newIframe.src = url.toString();

    // Make the new iframe invisible
    newIframe.classList.add(this.proxyClass);

    // Put it in the DOM so it loads the page
    this.iframeTarget.insertAdjacentElement('afterend', newIframe);
  }

  /**
   * Replaces the old iframe with the new iframe.
   * @param event The `load` event from the new iframe
   */
  replaceIframe(event: Event) {
    const id = this.iframeTarget.id;
    const newIframe = event.target as HTMLIFrameElement;

    // On Firefox, the `load` event is also fired even when the iframe has no
    // `src` attribute, like in the initial render from the server template. Do
    // not run the replacement logic in this case.
    if (!newIframe.src) return;

    // Restore scroll position with instant scroll to avoid flickering if the
    // previewed page has scroll-behavior: smooth.
    newIframe.contentWindow?.scroll({
      top: this.iframeTarget.contentWindow?.scrollY as number,
      left: this.iframeTarget.contentWindow?.scrollX as number,
      behavior: 'instant',
    });

    // Remove any other existing iframes. Normally there are two iframes at this
    // point, the old one and the new one. However, the `load` event may be fired
    // more than once for the same iframe, e.g. if the `src` attribute is changed
    // – in which case there is only one iframe and that is also the new one.
    this.iframeTargets.forEach((iframe) => {
      if (iframe !== newIframe) {
        iframe.remove();
      }
    });

    // Set the id and make the new iframe visible
    newIframe.id = id;
    newIframe.classList.remove(this.proxyClass);

    this.dispatch('loaded', { cancelable: false });

    runContentChecks();

    const onClickSelector = () => this.newTabTarget.click();
    runAccessibilityChecks(onClickSelector);

    // Ready for another update
    this.finishUpdate();
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

    // Ensure the width is set to the default size if the preview is unavailable,
    // or the currently selected device size if the preview is available.
    this.setPreviewWidth();

    if (!this.ready) {
      this.ready = true;
      this.dispatch('ready', { cancelable: false });
    }
    this.dispatch('updated', { cancelable: false });
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
    const link = event.currentTarget as HTMLAnchorElement;

    const valid = await this.setPreviewDataWithAlert();

    // Use the base URL value (without any params) as the target (identifier)
    // for the window, so that if the user switches between preview modes,
    // the same window will be reused.
    const url = new URL(link.href);
    url.search = '';
    window.open(link.href, url.toString()) as Window;

    return valid;
  }

  disconnect(): void {
    this.sidePanelContainer.removeEventListener('show', this.activatePreview);
    this.sidePanelContainer.removeEventListener('hide', this.deactivatePreview);

    this.checksSidePanel?.removeEventListener('show', this.activatePreview);
    this.checksSidePanel?.removeEventListener('hide', this.deactivatePreview);

    this.resizeObserver.disconnect();
  }
}
