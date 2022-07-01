import { gettext } from '../../utils/gettext';

function initPreview() {
  const previewPanel = document.querySelector('[data-preview-panel]');
  // Preview panel is not shown if the object does not have any preview modes
  if (!previewPanel) return;

  //
  // Preview size handling
  //

  const sizeInputs = previewPanel.querySelectorAll('[data-device-width]');
  const defaultSizeInput = previewPanel.querySelector('[data-default-size]');

  const setPreviewWidth = (width) => {
    const deviceWidth = width || defaultSizeInput.dataset.deviceWidth;
    previewPanel.style.setProperty('--preview-device-width', deviceWidth);
  };

  const togglePreviewSize = (event) => {
    const device = event.target.value;
    const deviceWidth = event.target.dataset.deviceWidth;

    setPreviewWidth(deviceWidth);

    // Ensure only one device class is applied
    previewPanel.className = `preview-panel preview-panel--${device}`;
    previewPanel.classList.toggle(
      'preview-panel--has-errors',
      previewPanel.hasAttribute('data-preview-error'),
    );
  };

  sizeInputs.forEach((input) =>
    input.addEventListener('change', togglePreviewSize),
  );

  const previewArea = previewPanel.querySelector('[data-preview-panel-area]');
  const resizeObserver = new ResizeObserver((entries) => {
    const area = entries[0];
    if (!area) return;
    const areaRect = area.contentRect;
    previewPanel.style.setProperty('--preview-area-width', areaRect.width);
  });

  resizeObserver.observe(previewArea);

  //
  // Preview data handling
  //
  // In order to make the preview truly reliable, the preview page needs
  // to be perfectly independent from the edit page,
  // from the browser perspective. To pass data from the edit page
  // to the preview page, we send the form after each change
  // and save it inside the user session.

  const newTabButton = previewPanel.querySelector('[data-preview-new-tab]');
  const loadingSpinner = previewPanel.querySelector('[data-preview-spinner]');
  const form = document.querySelector('[data-edit-form]');
  const previewUrl = previewPanel.dataset.action;
  const previewModeSelect = document.querySelector(
    '[data-preview-mode-select]',
  );
  let iframe = previewPanel.querySelector('[data-preview-iframe]');
  const iframeLastScroll = { top: 0, left: 0 };

  const updateIframeLastScroll = () => {
    if (!iframe.contentWindow) return;
    iframeLastScroll.top = iframe.contentWindow.scrollY;
    iframeLastScroll.left = iframe.contentWindow.scrollX;
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
      newIframe.contentWindow.scroll(iframeLastScroll);

      // Remove the old iframe and swap it with the new one
      iframe.remove();
      iframe = newIframe;

      // Make the new iframe visible
      newIframe.style = null;

      // Hide loading spinner
      loadingSpinner.classList.add('w-hidden');

      // Remove the load event listener so it doesn't fire when switching modes
      newIframe.removeEventListener('load', handleLoad);
    };

    newIframe.addEventListener('load', handleLoad);
  };

  const setPreviewData = () => {
    loadingSpinner.classList.remove('w-hidden');

    return fetch(previewUrl, {
      method: 'POST',
      body: new FormData(form),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.is_valid) {
          previewPanel.removeAttribute('data-preview-error');
        } else {
          previewPanel.setAttribute('data-preview-error', '');
        }

        updateIframeLastScroll();
        previewPanel.classList.toggle(
          'preview-panel--has-errors',
          !data.is_valid,
        );

        reloadIframe();
        return data.is_valid;
      })
      .catch((error) => {
        loadingSpinner.classList.add('w-hidden');
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

  if (previewPanel.dataset.autoUpdate === 'true') {
    let oldData = new FormData(form);
    const hasChanges = () => {
      const newData = new FormData(form);
      const oldPayload = new URLSearchParams(oldData).toString();
      const newPayload = new URLSearchParams(newData).toString();

      oldData = newData;
      return oldPayload !== newPayload;
    };

    let hasPendingRequest = false;
    setInterval(() => {
      // Do not check for preview update if an update request is still pending
      // and don't send a new request if the form hasn't changed
      if (hasPendingRequest || !hasChanges()) return;

      hasPendingRequest = true;
      setPreviewData().finally(() => {
        hasPendingRequest = false;
      });
    }, 500);
  }

  //
  // Preview mode handling
  //

  const handlePreviewModeChange = (event) => {
    const mode = event.target.value;
    const url = new URL(iframe.src);
    url.searchParams.set('mode', mode);

    // Remember the last scroll position
    // because setting the src attribute will reload the iframe
    updateIframeLastScroll();
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
