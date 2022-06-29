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
    const hasErrors = previewPanel.hasAttribute('data-preview-error');
    const deviceWidth = hasErrors ? null : event.target.dataset.deviceWidth;

    setPreviewWidth(deviceWidth);

    // Ensure only one device class is applied
    previewPanel.className = `preview-panel preview-panel--${device}`;
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

  const refreshButton = previewPanel.querySelector('[data-refresh-preview]');
  const newTabButton = previewPanel.querySelector('[data-preview-new-tab]');
  const iframe = previewPanel.querySelector('[data-preview-iframe]');
  const form = document.querySelector('[data-edit-form]');
  const previewUrl = previewPanel.dataset.action;
  const previewModeSelect = document.querySelector(
    '[data-preview-mode-select]',
  );

  const setPreviewData = () =>
    fetch(previewUrl, {
      method: 'POST',
      body: new FormData(form),
    }).then((response) =>
      response.json().then((data) => {
        if (data.is_valid) {
          previewPanel.removeAttribute('data-preview-error');
        } else {
          previewPanel.setAttribute('data-preview-error', '');
          setPreviewWidth(); // Reset to default size
        }

        iframe.contentWindow.location.reload();
        return data.is_valid;
      }),
    );

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

  refreshButton.addEventListener('click', handlePreview);
  newTabButton.addEventListener('click', handlePreviewInNewTab);

  if (previewPanel.dataset.autoUpdate === 'true') {
    // Form data is changed when field values are changed (change event),
    // and we need to delay setPreviewData when typing to avoid useless extra
    // AJAX requests (so we postpone setPreviewData when keyup occurs).

    let autoUpdatePreviewDataTimeout;
    const autoUpdatePreview = () => {
      clearTimeout(autoUpdatePreviewDataTimeout);
      autoUpdatePreviewDataTimeout = setTimeout(setPreviewData, 1000);
    };

    ['change', 'keyup'].forEach((e) =>
      form.addEventListener(e, autoUpdatePreview),
    );
  }

  //
  // Preview mode handling
  //

  const handlePreviewModeChange = (event) => {
    const mode = event.target.value;
    const url = new URL(iframe.src);
    url.searchParams.set('mode', mode);
    // Make sure data is up-to-date before changing the preview mode.
    handlePreview().then(() => {
      iframe.src = url.toString();
      url.searchParams.delete('in_preview_panel');
      newTabButton.href = url.toString();
    });
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
