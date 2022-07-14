import { gettext } from '../../utils/gettext';

function initPreview() {
  const previewSidePanel = document.querySelector(
    '[data-side-panel="preview"]',
  );

  // Preview side panel is not shown if the object does not have any preview modes
  if (!previewSidePanel) return;

  // Get settings from the preview_settings template tag
  const settings = JSON.parse(
    document.getElementById('wagtail-preview-settings').textContent,
  );

  // The previewSidePanel is a generic container for side panels,
  // the content of the preview panel itself is in a child element
  const previewPanel = previewSidePanel.querySelector('[data-preview-panel]');

  //
  // Preview size handling
  //

  const sizeInputs = previewPanel.querySelectorAll('[data-device-width]');
  const defaultSizeInput = previewPanel.querySelector('[data-default-size]');

  const setPreviewWidth = (width) => {
    const isUnavailable = previewPanel.classList.contains(
      'preview-panel--unavailable',
    );

    let deviceWidth = width;
    // Reset to default size if width is falsy or preview is unavailable
    if (!width || isUnavailable) {
      deviceWidth = defaultSizeInput.dataset.deviceWidth;
    }

    previewPanel.style.setProperty('--preview-device-width', deviceWidth);
  };

  const togglePreviewSize = (event) => {
    const device = event.target.value;
    const deviceWidth = event.target.dataset.deviceWidth;

    setPreviewWidth(deviceWidth);

    // Ensure only one device class is applied
    sizeInputs.forEach((input) => {
      previewPanel.classList.toggle(
        `preview-panel--${input.value}`,
        input.value === device,
      );
    });
  };

  sizeInputs.forEach((input) =>
    input.addEventListener('change', togglePreviewSize),
  );

  const resizeObserver = new ResizeObserver((entries) =>
    previewPanel.style.setProperty(
      '--preview-panel-width',
      entries[0].contentRect.width,
    ),
  );
  resizeObserver.observe(previewPanel);

  //
  // Preview data handling
  //
  // In order to make the preview truly reliable, the preview page needs
  // to be perfectly independent from the edit page,
  // from the browser perspective. To pass data from the edit page
  // to the preview page, we send the form after each change
  // and save it inside the user session.

  const newTabButton = previewPanel.querySelector('[data-preview-new-tab]');
  const refreshButton = previewPanel.querySelector('[data-refresh-preview]');
  const loadingSpinner = previewPanel.querySelector('[data-preview-spinner]');
  const form = document.querySelector('[data-edit-form]');
  const previewUrl = previewPanel.dataset.action;
  const previewModeSelect = document.querySelector(
    '[data-preview-mode-select]',
  );
  let iframe = previewPanel.querySelector('[data-preview-iframe]');
  let spinnerTimeout;
  let hasPendingUpdate = false;

  const finishUpdate = () => {
    clearTimeout(spinnerTimeout);
    loadingSpinner.classList.add('w-hidden');
    hasPendingUpdate = false;
  };

  const reloadIframe = () => {
    // Instead of reloading the iframe, we're replacing it with a new iframe to
    // prevent flashing

    // Create a new invisible iframe element
    const newIframe = document.createElement('iframe');
    newIframe.style.width = 0;
    newIframe.style.height = 0;
    newIframe.style.opacity = 0;
    newIframe.style.position = 'absolute';
    newIframe.src = iframe.src;

    // Put it in the DOM so it loads the page
    iframe.insertAdjacentElement('afterend', newIframe);

    const handleLoad = () => {
      // Copy all attributes from the old iframe to the new one,
      // except src as that will cause the iframe to be reloaded
      Array.from(iframe.attributes).forEach((key) => {
        if (key.nodeName === 'src') return;
        newIframe.setAttribute(key.nodeName, key.nodeValue);
      });

      // Restore scroll position
      newIframe.contentWindow.scroll(
        iframe.contentWindow.scrollX,
        iframe.contentWindow.scrollY,
      );

      // Remove the old iframe and swap it with the new one
      iframe.remove();
      iframe = newIframe;

      // Make the new iframe visible
      newIframe.style = null;

      // Ready for another update
      finishUpdate();

      // Remove the load event listener so it doesn't fire when switching modes
      newIframe.removeEventListener('load', handleLoad);
    };

    newIframe.addEventListener('load', handleLoad);
  };

  const setPreviewData = () => {
    hasPendingUpdate = true;
    spinnerTimeout = setTimeout(
      () => loadingSpinner.classList.remove('w-hidden'),
      2000,
    );

    return fetch(previewUrl, {
      method: 'POST',
      body: new FormData(form),
    })
      .then((response) => response.json())
      .then((data) => {
        previewPanel.classList.toggle(
          'preview-panel--has-errors',
          !data.is_valid,
        );
        previewPanel.classList.toggle(
          'preview-panel--unavailable',
          !data.is_available,
        );

        if (data.is_valid) {
          reloadIframe();
        } else {
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

  const handlePreviewInNewTab = (event) => {
    event.preventDefault();
    const previewWindow = window.open('', previewUrl);
    previewWindow.focus();

    handlePreview().then((success) => {
      if (success) {
        const url = new URL(newTabButton.href);
        previewWindow.document.location = url.toString();
      } else {
        window.focus();
        previewWindow.close();
      }
    });
  };

  newTabButton.addEventListener('click', handlePreviewInNewTab);

  if (refreshButton) {
    refreshButton.addEventListener('click', handlePreview);
  }

  if (settings.WAGTAIL_AUTO_UPDATE_PREVIEW) {
    let oldPayload = new URLSearchParams(new FormData(form)).toString();
    let updateInterval;

    const hasChanges = () => {
      const newPayload = new URLSearchParams(new FormData(form)).toString();
      const changed = oldPayload !== newPayload;

      oldPayload = newPayload;
      return changed;
    };

    const checkAndUpdatePreview = () => {
      // Do not check for preview update if an update request is still pending
      // and don't send a new request if the form hasn't changed
      if (hasPendingUpdate || !hasChanges()) return;
      setPreviewData();
    };

    previewSidePanel.addEventListener('show', () => {
      // Immediately update the preview when the panel is opened
      checkAndUpdatePreview();

      // Only set the interval while the panel is shown
      updateInterval = setInterval(
        checkAndUpdatePreview,
        settings.WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL,
      );
    });

    previewSidePanel.addEventListener('hide', () => {
      clearInterval(updateInterval);
    });
  }

  //
  // Preview mode handling
  //

  const handlePreviewModeChange = (event) => {
    const mode = event.target.value;
    const url = new URL(iframe.src);
    url.searchParams.set('mode', mode);

    iframe.src = url.toString();
    url.searchParams.delete('in_preview_panel');
    newTabButton.href = url.toString();

    // Make sure data is updated
    handlePreview();
  };

  if (previewModeSelect) {
    previewModeSelect.addEventListener('change', handlePreviewModeChange);
  }

  // Make sure current preview data in session exists and is up-to-date.
  setPreviewData();
  setPreviewWidth();
}

document.addEventListener('DOMContentLoaded', () => {
  initPreview();
});
