import axe from 'axe-core';

import { Controller } from '@hotwired/stimulus';
import type { ContextObject } from 'axe-core';
import {
  getAxeConfiguration,
  getA11yReport,
  renderA11yResults,
  WagtailAxeConfiguration,
  addCustomChecks,
} from '../includes/a11y-result';
import { wagtailPreviewPlugin } from '../includes/previewPlugin';
import {
  ContentExtractorOptions,
  getPreviewContent,
  getReadingTime,
  getLIXScore,
  getReadabilityScore,
  getWordCount,
  renderContentMetrics,
} from '../includes/contentMetrics';
import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { gettext } from '../utils/gettext';
import type { ProgressController } from './ProgressController';
import { GetScrollPosition, getWagtailMessage } from '../utils/message';
import { debounce, DebouncibleFunction } from '../utils/debounce';

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
 * @fires PreviewController#content - When the content of the preview iframe is extracted to be analyzed.
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
 * @property {object} detail
 * @property {PreviewDataResponse} detail.data - The response data that indicates whether the submitted data was valid and whether the preview is available.
 * @property {string} name - `w-preview:json`
 *
 * @event PreviewController#error
 * @type {CustomEvent}
 * @property {object} detail
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
 * @event PreviewController#content
 * @type {CustomEvent}
 * @property {string} name - `w-preview:content`
 * @property {object} detail
 * @property {ExtractedContent} detail.content - The extracted content from the preview iframe.
 * @property {ContentMetrics} detail.metrics - The calculated metrics of the preview content.
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
    stale: { default: true, type: Boolean },
    url: { default: '', type: String },
  };

  static outlets = ['w-progress'];

  /** The device size width to use when the preview is not available. */
  static fallbackWidth = PREVIEW_UNAVAILABLE_WIDTH.toString();

  /**
   * The time tolerance between the iframe's `load` event and the scroll
   * restoration completion, which may not be instantaneous for cross-domain
   * preview iframes.
   */
  static scrollRestoreTimeout = 10_000; // 10 seconds

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
  /**
   * All preview `<iframe>`s that are currently in the DOM.
   * This contains the currently displayed `<iframe>` and may also contain
   * the new `<iframe>` that will replace the current one.
   */
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

  /**
   * Interval in milliseconds when the form is checked for changes.
   * Also used as the debounce duration for the update request.
   */
  declare readonly autoUpdateIntervalValue: number;
  /** Key for storing the last selected device size in localStorage. */
  declare readonly deviceLocalStorageKeyValue: string;
  /** CSS property for setting the device width. */
  declare readonly deviceWidthPropertyValue: string;
  /** CSS property for the current width of the panel, to maintain the device scaling. */
  declare readonly panelWidthPropertyValue: string;
  /**
   * URL for rendering the preview, defaults to `urlValue`.
   * Useful for headless setups where the front-end may be hosted at a different URL.
   */
  declare renderUrlValue: string;
  /** Whether the preview data is considered stale and needs an update. */
  declare staleValue: boolean;
  /** URL for updating the preview data. Also used for rendering the preview if `renderUrlValue` is unset. */
  declare readonly urlValue: string;

  // Outlets

  /** ProgressController for the refresh button that may be displayed when auto-update is turned off. */
  declare readonly wProgressOutlet: ProgressController;
  declare readonly hasWProgressOutlet: boolean;

  // Instance variables with initial values set in connect()

  /** Template for rendering a row of accessibility check results. */
  declare a11yRowTemplate: HTMLTemplateElement | null;
  /** Configuration for Axe. */
  declare axeConfig: WagtailAxeConfiguration | null;
  /** Configuration for Wagtail's Axe content extractor plugin instance. */
  declare contentExtractorOptions: ContentExtractorOptions;
  /** Container for rendering content checks results. */
  declare checksPanel: HTMLElement | null;
  /** Content checks counter inside the checks panel. */
  declare checksPanelCounter: HTMLElement | null;
  /** Side panel for content checks. */
  declare checksSidePanel: HTMLDivElement | null;
  /** Content checks counter on the side panel toggle. */
  declare checksToggleCounter: HTMLElement | null;
  /** Whether content checks are enabled. */
  declare contentChecksEnabled: boolean;
  /** Main editor form. */
  declare editForm: HTMLFormElement;
  /**
   * ResizeObserver to observe when the panel is resized
   * so we can maintain the device size scaling.
   */
  declare resizeObserver: ResizeObserver;
  /**
   * Side panel element of the preview panel, i.e. the element with the
   * `data-side-panel` attribute. Useful for listening to show/hide events.
   * Normally, this is the parent element of the controller element.
   */
  declare sidePanelContainer: HTMLDivElement;

  declare setPreviewDataLazy: DebouncibleFunction<
    () => Promise<boolean> | undefined
  >;

  // Instance variables with initial values set here

  /**
   * Whether the preview is ready for further updates.
   *
   * @remarks
   * The preview data is stored in the session, which means:
   *
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

  /**
   * Whether the preview is currently available. This is used to distinguish
   * whether we are rendering a preview or the "Preview is not available"
   * screen. So even if the preview is currently outdated, this is still `true`
   * as long as the preview data is available and the preview is rendered (e.g.
   * if the form becomes invalid after the preview is successfully rendered).
   */
  available = true;

  /** Timeout before displaying the loading spinner. */
  spinnerTimeout: ReturnType<typeof setTimeout> | null = null;

  /**
   * Promise for the current update request. This is resolved as soon as the
   * update request is successful, so the preview iframe may not have been
   * fully reloaded.
   */
  updatePromise: Promise<boolean> | null = null;

  /**
   * Promise for the current iframe reload. This is resolved when the new
   * iframe's `load` event is fired and the scroll position has been restored.
   */
  reloadPromise: Promise<void> | null = null;

  /** Resolver function for the current iframe reload promise. */
  #reloadPromiseResolve: (() => void) | null = null;

  /**
   * Promise for the current content checks request. This resolved when both
   * the content checks and the accessibility checks are completed. Useful for
   * queueing the checks, as Axe does not allow concurrent runs.
   */
  contentChecksPromise: Promise<void> | null = null;

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

  get shouldAutoUpdate() {
    return (
      // Auto-update is enabled
      this.autoUpdateIntervalValue > 0 &&
      // And either the preview panel or the checks side panel (if enabled) is visible
      (!this.sidePanelContainer.hidden ||
        (this.checksSidePanel && !this.checksSidePanel.hidden))
    );
  }

  initialize(): void {
    this.checkAndUpdatePreview = this.checkAndUpdatePreview.bind(this);
    this.runChecks = this.runChecks.bind(this);
    this.setPreviewData = this.setPreviewData.bind(this);
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

    this.sidePanelContainer.addEventListener(
      'show',
      this.checkAndUpdatePreview,
    );

    this.setUpContentChecks();

    this.restoreLastSavedPreferences();

    if (
      !this.sidePanelContainer.hidden ||
      (this.checksSidePanel && !this.checksSidePanel.hidden)
    ) {
      this.checkAndUpdatePreview();
    }
  }

  setUpContentChecks() {
    this.checksSidePanel = document.querySelector('[data-side-panel="checks"]');
    this.a11yRowTemplate = document.querySelector<HTMLTemplateElement>(
      '#w-a11y-result-row-template',
    );
    this.checksPanel = document.querySelector<HTMLElement>(
      '[data-checks-panel]',
    );
    this.axeConfig = getAxeConfiguration(document.body);
    this.checksToggleCounter = document.querySelector<HTMLElement>(
      '[data-side-panel-toggle="checks"] [data-side-panel-toggle-counter]',
    );
    this.checksPanelCounter = document.querySelector<HTMLElement>(
      '[data-side-panel="checks"] [data-a11y-result-count]',
    );

    if (
      !(
        this.checksSidePanel &&
        this.checksPanel &&
        this.a11yRowTemplate &&
        this.axeConfig &&
        this.checksToggleCounter &&
        this.checksPanelCounter
      )
    ) {
      this.contentChecksEnabled = false;
      return;
    }

    // Ensure we only test within the preview iframe, but nonetheless with the correct selectors.
    this.axeConfig.context.include = {
      fromFrames: ['#w-preview-iframe'].concat(
        this.axeConfig.context.include as string[],
      ),
    } as ContextObject['include'];

    if ((this.axeConfig.context.exclude as string[])?.length > 0) {
      this.axeConfig.context.exclude = {
        fromFrames: ['#w-preview-iframe'].concat(
          this.axeConfig.context.exclude as string[],
        ),
      } as ContextObject['exclude'];
    }

    this.contentExtractorOptions = {
      targetElement: 'main, [role="main"]',
    };

    axe.configure(addCustomChecks(this.axeConfig.spec));
    axe.registerPlugin(wagtailPreviewPlugin);

    this.checksSidePanel.addEventListener('show', this.checkAndUpdatePreview);

    // Add the message event listener here instead of using a Stimulus action,
    // as message events may originate from other sources and thus will add
    // noise to the console when used as an action.
    window.addEventListener('message', this.runChecks);
    this.contentChecksEnabled = true;
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
      // Initialize with the default device if the last one cannot be restored.
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
   * Like `setPreviewData`, but only updates the preview if the form has not changed.
   * @returns whether the data is valid
   */
  async checkAndUpdatePreview() {
    // If there are no changes, return the existing update promise (if any)
    if (!this.staleValue) return this.updatePromise;
    return this.setPreviewData();
  }

  /**
   * Marks the preview data as stale, indicating it needs an update.
   * Accepts an optional `stale` parameter to explicitly override the value.
   */
  setStale(event?: Event & { params?: { stale: boolean } }) {
    this.staleValue = event?.params?.stale ?? true;
  }

  staleValueChanged(newValue: boolean) {
    if (this.ready && newValue && this.shouldAutoUpdate) {
      this.setPreviewDataLazy();
    }
  }

  autoUpdateIntervalValueChanged(newValue?: number) {
    // Update the debounce function with the new interval, without cancelling
    // any pending calls to ensure they are still executed.
    this.setPreviewDataLazy = debounce(this.setPreviewData, newValue);
  }

  /**
   * Updates the preview data in the session. If the data is valid, the preview
   * iframe will be reloaded. If the data is invalid, the preview panel will
   * display an error message.
   * @returns whether the data is valid
   */
  setPreviewData() {
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
    this.staleValue = false;

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
    this.reloadPromise = new Promise<void>((resolve) => {
      this.#reloadPromiseResolve = resolve;
    });

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
  async replaceIframe(event: Event) {
    const id = this.iframeTarget.id;
    const newIframe = event.target as HTMLIFrameElement;

    // On Firefox, the `load` event is also fired even when the iframe has no
    // `src` attribute, like in the initial render from the server template. Do
    // not run the replacement logic in this case.
    if (!newIframe.src) return;

    // On subsequent loads, restore the scroll position from the old iframe
    if (this.ready) await this.restoreScrollPosition(newIframe);

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

    // Finish the update process. Instead of calling `runChecks()` here,
    // accessibility and content checks will be triggered by the userbar in the
    // new iframe via the `w-userbar:axe-ready` message event. This ensures that
    // Axe in this window does not instruct the new iframe's Axe to immediately
    // run the checks, which might fail if it is still running the initial
    // checks as part of the userbar initialization.
    this.finishUpdate();
  }

  /**
   * Restores the scroll position from the old iframe to the new one.
   * For same-origin iframes, this is done by calling `scroll()` on the new
   * iframe's content window with the scroll position of the old iframe.
   * For cross-origin iframes, this is done by using the postMessage API to
   * request the scroll position from the old iframe and send it to the new one.
   * @param newIframe The new iframe element that will replace the old one.
   * @returns a Promise that resolves when the scroll position is restored or
   * the timeout has lapsed.
   */
  async restoreScrollPosition(newIframe: HTMLIFrameElement): Promise<void> {
    const isCrossOrigin = { oldIframe: false, newIframe: false };
    // Do try/catch for each iframe so we know which of the iframes are cross-origin
    try {
      isCrossOrigin.oldIframe =
        !this.iframeTarget.contentWindow?.location.origin;
    } catch {
      isCrossOrigin.oldIframe = true;
    }
    try {
      isCrossOrigin.newIframe = !newIframe.contentWindow?.location.origin;
    } catch {
      isCrossOrigin.newIframe = true;
    }

    // Origins mismatch, something has gone wrong, skip scroll restoration.
    if (isCrossOrigin.oldIframe !== isCrossOrigin.newIframe) {
      return Promise.resolve();
    }

    // Normal same-domain for both iframes
    if (!isCrossOrigin.oldIframe && !isCrossOrigin.newIframe) {
      // Restore scroll position with instant scroll to avoid flickering if the
      // previewed page has scroll-behavior: smooth.
      newIframe.contentWindow?.scroll({
        top: this.iframeTarget.contentWindow?.scrollY as number,
        left: this.iframeTarget.contentWindow?.scrollX as number,
        behavior: 'instant',
      });
      return Promise.resolve();
    }

    // Both iframes are likely cross-domain, e.g. in a headless setup, in which
    // case we cannot call `scroll()` directly. Use the postMessage API
    // instead to request the scroll position from the old iframe and send it
    // to the new iframe.
    return new Promise<void>((resolve) => {
      const scrollHandler = (event: MessageEvent) => {
        const data = getWagtailMessage(event);
        if (!data) return;

        switch (data.type) {
          case 'w-preview:request-scroll':
            // The new iframe is requesting to scroll to the last scroll position
            // Get the last scroll position from the old iframe
            this.iframeTarget.contentWindow?.postMessage(
              {
                wagtail: {
                  type: 'w-preview:get-scroll-position',
                } as GetScrollPosition,
              },
              data.origin,
            );
            break;
          case 'w-preview:set-scroll-position':
            // The old iframe responded with the last scroll position
            // Set the scroll position on the new iframe
            newIframe.contentWindow?.postMessage(
              { wagtail: data },
              data.origin,
            );

            // Done, remove the event listener and resolve the promise
            window.removeEventListener('message', scrollHandler);
            resolve();
            break;
          default:
            break;
        }
      };

      window.addEventListener('message', scrollHandler);

      // If the cross-frame communication takes too long,
      // resolve the promise to avoid hanging the preview indefinitely
      setTimeout(() => {
        window.removeEventListener('message', scrollHandler);
        resolve();
      }, PreviewController.scrollRestoreTimeout);
    });
  }

  /**
   * Runs the content and accessibility checks.
   * This is called when the iframe sends a message event from the userbar
   * indicating that it has finished running the checks within itself.
   * @param event The message event from the userbar
   */
  async runChecks(event?: MessageEvent<{ wagtail: { type: string } }>) {
    // If the method acts as a MessageEvent handler, ensure the event is
    // from the correct source and type, to avoid running the checks excessively.
    // Other events do not need to be checked, as we assume it's intentional
    // (e.g. a custom button that re-runs the checks on click).
    if (event && event.type === 'message') {
      const data = getWagtailMessage(event);
      // Ignore messages that are not from the userbar indicating axe is ready
      if (data?.type !== 'w-userbar:axe-ready')
        return this.contentChecksPromise;
    }

    // If the content checks are already running, wait for them to finish before
    // re-running them, as Axe does not allow concurrent runs.
    if (this.contentChecksPromise) {
      await this.contentChecksPromise;
    }

    this.contentChecksPromise = (async () => {
      await this.runAccessibilityChecks();
      await this.runContentChecks();
      this.contentChecksPromise = null;
    })();

    return this.contentChecksPromise;
  }

  /**
   * Runs the accessibility checks using Axe.
   */
  async runAccessibilityChecks() {
    const { results, a11yErrorsNumber } = await getA11yReport(this.axeConfig!);

    this.checksToggleCounter!.textContent = a11yErrorsNumber.toString();
    this.checksToggleCounter!.hidden = a11yErrorsNumber === 0;
    this.checksPanelCounter!.textContent = a11yErrorsNumber.toString();
    this.checksPanelCounter!.classList.toggle(
      'has-errors',
      a11yErrorsNumber > 0,
    );

    renderA11yResults(
      this.checksPanel!,
      results,
      this.axeConfig!,
      this.a11yRowTemplate!,
      () => this.newTabTarget.click(),
    );
  }

  /**
   * Runs the content checks by extracting the content from the preview iframe
   * using an Axe plugin and calculating content metrics.
   */
  async runContentChecks() {
    const content = await this.extractContent();

    // If for any reason the plugin fails to return the content (e.g. the
    // previewed page shows an error response), skip doing anything with it.
    if (!content) return;

    const wordCount = getWordCount(content.lang, content.innerText);
    const readingTime = getReadingTime(content.lang, wordCount);
    const lixScore = getLIXScore(content.lang, content.innerText);
    const readabilityScore = getReadabilityScore(lixScore);
    const metrics = { wordCount, readingTime, lixScore, readabilityScore };

    this.dispatch('content', { detail: { content, metrics } });

    renderContentMetrics(metrics);
  }

  /**
   * Extracts the rendered content from the preview iframe via an Axe plugin.
   * @param options Options object for extracting the content. Supported options:
   * - `targetElement`: CSS selector for the element to extract content from. Defaults to `main, [role="main"]`.
   * @returns An `ExtractedContent` object with `lang`, `innerText`, and `innerHTML` properties.
   */
  async extractContent(options?: ContentExtractorOptions) {
    if (!this.ready) {
      // Preview panel likely hasn't been opened, force an update to ensure
      // the preview iframe is loaded with the current data.
      await this.checkAndUpdatePreview();
      await this.reloadPromise;
    }

    return getPreviewContent(options || this.contentExtractorOptions);
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

    this.#reloadPromiseResolve?.();
    this.reloadPromise = null;
    this.#reloadPromiseResolve = null;
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
    this.sidePanelContainer.removeEventListener(
      'show',
      this.checkAndUpdatePreview,
    );

    if (this.contentChecksEnabled) {
      window.removeEventListener('message', this.runChecks);
      this.checksSidePanel!.removeEventListener(
        'show',
        this.checkAndUpdatePreview,
      );
    }

    this.resizeObserver.disconnect();
  }
}
