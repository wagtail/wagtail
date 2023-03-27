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
  static targets = ['size', 'newTab', 'spinner', 'refresh', 'mode', 'iframe'];

  declare readonly sizeTargets: HTMLInputElement[];
  declare readonly newTabTarget: HTMLAnchorElement;
  declare readonly spinnerTarget: HTMLDivElement;
  declare readonly hasRefreshTarget: boolean;
  declare readonly refreshTarget: HTMLButtonElement;
  declare readonly hasModeTarget: boolean;
  declare readonly modeTarget: HTMLSelectElement;
  declare readonly iframeTarget: HTMLIFrameElement;
  declare readonly iframeTargets: HTMLIFrameElement[];

  connect() {
    const checksSidePanel = document.querySelector(
      '[data-side-panel="checks"]',
    );

    //
    // Preview size handling
    //

    const defaultSizeInput =
      this.sizeTargets.find((input) => 'defaultSize' in input.dataset) ||
      this.sizeTargets[0];

    const setPreviewWidth = (width?: string) => {
      const isUnavailable = this.element.classList.contains(
        'preview-panel--unavailable',
      );

      let deviceWidth = width;
      // Reset to default size if width is falsy or preview is unavailable
      if (!width || isUnavailable) {
        deviceWidth = defaultSizeInput.dataset.deviceWidth;
      }

      this.element.style.setProperty(
        '--preview-device-width',
        deviceWidth as string,
      );
    };

    const togglePreviewSize = (event: Event) => {
      const target = event.target as HTMLInputElement;
      const device = target.value;
      const deviceWidth = target.dataset.deviceWidth;

      setPreviewWidth(deviceWidth);
      try {
        localStorage.setItem('wagtail:preview-panel-device', device);
      } catch (e) {
        // Skip saving the device if localStorage fails.
      }

      // Ensure only one device class is applied
      this.sizeTargets.forEach((input) => {
        this.element.classList.toggle(
          `preview-panel--${input.value}`,
          input.value === device,
        );
      });
    };

    this.sizeTargets.forEach((input) =>
      input.addEventListener('change', togglePreviewSize),
    );

    const resizeObserver = new ResizeObserver((entries) =>
      this.element.style.setProperty(
        '--preview-panel-width',
        entries[0].contentRect.width.toString(),
      ),
    );
    resizeObserver.observe(this.element);

    //
    // Preview data handling
    //
    // In order to make the preview truly reliable, the preview page needs
    // to be perfectly independent from the edit page,
    // from the browser perspective. To pass data from the edit page
    // to the preview page, we send the form after each change
    // and save it inside the user session.

    const form = document.querySelector<HTMLFormElement>(
      '[data-edit-form]',
    ) as HTMLFormElement;
    const previewUrl = this.element.dataset.action as string;
    let spinnerTimeout: ReturnType<typeof setTimeout>;
    let hasPendingUpdate = false;
    let cleared = false;

    const finishUpdate = () => {
      clearTimeout(spinnerTimeout);
      this.spinnerTarget.classList.add('w-hidden');
      hasPendingUpdate = false;
    };

    const reloadIframe = () => {
      // Instead of reloading the iframe, we're replacing it with a new iframe to
      // prevent flashing

      // Create a new invisible iframe element
      const newIframe = document.createElement('iframe');
      const url = new URL(previewUrl, window.location.href);
      if (this.hasModeTarget) {
        url.searchParams.set('mode', this.modeTarget.value);
      }
      url.searchParams.set('in_preview_panel', 'true');
      newIframe.style.width = '0';
      newIframe.style.height = '0';
      newIframe.style.opacity = '0';
      newIframe.style.position = 'absolute';
      newIframe.src = url.toString();

      // Put it in the DOM so it loads the page
      this.iframeTarget.insertAdjacentElement('afterend', newIframe);

      const handleLoad = () => {
        // Copy all attributes from the old iframe to the new one,
        // except src as that will cause the iframe to be reloaded
        Array.from(this.iframeTarget.attributes).forEach((key) => {
          if (key.nodeName === 'src') return;
          newIframe.setAttribute(key.nodeName, key.nodeValue as string);
        });

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
        finishUpdate();

        // Remove the load event listener so it doesn't fire when switching modes
        newIframe.removeEventListener('load', handleLoad);

        const onClickSelector = () => this.newTabTarget.click();
        runAccessibilityChecks(onClickSelector);
      };

      newIframe.addEventListener('load', handleLoad);
    };

    const clearPreviewData = () =>
      fetch(previewUrl, {
        headers: {
          [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
        },
        method: 'DELETE',
      });

    const setPreviewData = () => {
      // Bail out if there is already a pending update
      if (hasPendingUpdate) return Promise.resolve();

      hasPendingUpdate = true;
      spinnerTimeout = setTimeout(
        () => this.spinnerTarget.classList.remove('w-hidden'),
        2000,
      );

      return fetch(previewUrl, {
        method: 'POST',
        body: new FormData(form),
      })
        .then((response) => response.json())
        .then((data) => {
          this.element.classList.toggle(
            'preview-panel--has-errors',
            !data.is_valid,
          );
          this.element.classList.toggle(
            'preview-panel--unavailable',
            !data.is_available,
          );

          if (!data.is_available) {
            // Ensure the 'Preview not available' message is not scaled down
            setPreviewWidth();
          }

          if (data.is_valid) {
            reloadIframe();
          } else if (!cleared) {
            clearPreviewData();
            cleared = true;
            reloadIframe();
          } else {
            // Finish the process when the data is invalid to prepare for the next update
            // and avoid elements like the loading spinner to be shown indefinitely
            finishUpdate();
          }

          return data.is_valid;
        })
        .catch((error) => {
          finishUpdate();
          // Re-throw error so it can be handled by handlePreview
          throw error;
        });
    };

    const handlePreview = () =>
      setPreviewData().catch(() => {
        // eslint-disable-next-line no-alert
        window.alert(gettext('Error while sending preview data.'));
      });

    const handlePreviewInNewTab = (event: MouseEvent) => {
      event.preventDefault();
      const previewWindow = window.open('', previewUrl) as Window;
      previewWindow.focus();

      handlePreview().then((success) => {
        if (success) {
          const url = new URL(this.newTabTarget.href);
          previewWindow.document.location = url.toString();
        } else {
          window.focus();
          previewWindow.close();
        }
      });
    };

    this.newTabTarget.addEventListener('click', handlePreviewInNewTab);

    if (this.hasRefreshTarget) {
      this.refreshTarget.addEventListener('click', handlePreview);
    }

    // This controller is encapsulated as a child of the side panel element,
    // so we need to listen to the show/hide events on the parent element
    // (the one with [data-side-panel]).
    // If we had support for data-controller attribute on the side panels,
    // we could remove the intermediary element and make the [data-side-panel]
    // element to also act as the controller.
    const sidePanelContainer = this.element.parentElement as HTMLDivElement;

    if (WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW) {
      // Start with an empty payload so that when checkAndUpdatePreview is called
      // for the first time when the panel is opened, it will always update the preview
      let oldPayload = '';
      let updateInterval: ReturnType<typeof setInterval>;

      const hasChanges = () => {
        // https://github.com/microsoft/TypeScript/issues/30584
        const newPayload = new URLSearchParams(
          new FormData(form) as unknown as Record<string, string>,
        ).toString();
        const changed = oldPayload !== newPayload;

        oldPayload = newPayload;
        return changed;
      };

      // Call setPreviewData only if no changes have been made within the interval
      const debouncedSetPreviewData = debounce(
        setPreviewData,
        WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL,
      );

      const checkAndUpdatePreview = () => {
        // Do not check for preview update if an update request is still pending
        // and don't send a new request if the form hasn't changed
        if (hasPendingUpdate || !hasChanges()) return;
        debouncedSetPreviewData();
      };

      sidePanelContainer.addEventListener('show', () => {
        // Immediately update the preview when the panel is opened
        checkAndUpdatePreview();

        // Only set the interval while the panel is shown
        // This interval performs the checks for changes but not necessarily the
        // update itself
        updateInterval = setInterval(
          checkAndUpdatePreview,
          WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL,
        );
      });

      // Use the same processing as the preview panel.
      checksSidePanel?.addEventListener('show', () => {
        checkAndUpdatePreview();
        updateInterval = setInterval(
          checkAndUpdatePreview,
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
    } else {
      // Even if the preview is not updated automatically, we still need to
      // initialise the preview data when the panel is shown
      sidePanelContainer.addEventListener('show', () => {
        setPreviewData();
      });
      checksSidePanel?.addEventListener('show', () => {
        setPreviewData();
      });
    }

    //
    // Preview mode handling
    //

    const handlePreviewModeChange = (event: Event) => {
      const mode = (event.target as HTMLSelectElement).value;
      const url = new URL(previewUrl, window.location.href);
      url.searchParams.set('mode', mode);
      url.searchParams.delete('in_preview_panel');
      this.newTabTarget.href = url.toString();

      // Make sure data is updated
      handlePreview();
    };

    if (this.hasModeTarget) {
      this.modeTarget.addEventListener('change', handlePreviewModeChange);
    }

    // Remember last selected device size
    let lastDevice: string | null = null;
    try {
      lastDevice = localStorage.getItem('wagtail:preview-panel-device');
    } catch (e) {
      // Initialise with the default device if the last one cannot be restored.
    }
    const lastDeviceInput =
      this.sizeTargets.find((input) => input.value === lastDevice) ||
      defaultSizeInput;
    lastDeviceInput.click();
  }
}
