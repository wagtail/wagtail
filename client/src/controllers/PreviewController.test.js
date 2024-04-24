import { Application } from '@hotwired/stimulus';
import { PreviewController } from './PreviewController';

jest.mock('../config/wagtailConfig.js', () => ({
  WAGTAIL_CONFIG: {
    CSRF_HEADER_NAME: 'X-CSRFToken',
    CSRF_TOKEN: 'test-token',
  },
}));

describe('PreviewController', () => {
  let application;
  let windowSpy;
  const originalWindow = { ...window };
  const mockWindow = (props) =>
    windowSpy.mockImplementation(() => ({
      ...originalWindow,
      ...props,
    }));
  const resizeObserverMockObserve = jest.fn();
  const resizeObserverMockUnobserve = jest.fn();
  const resizeObserverMockDisconnect = jest.fn();

  const ResizeObserverMock = jest.fn().mockImplementation(() => ({
    observe: resizeObserverMockObserve,
    unobserve: resizeObserverMockUnobserve,
    disconnect: resizeObserverMockDisconnect,
  }));

  global.ResizeObserver = ResizeObserverMock;

  const url = '/admin/pages/1/edit/preview/';
  const spinner = /* html */ `
    <div data-w-preview-target="spinner" hidden>
      <svg class="icon icon-spinner default" aria-hidden="true">
        <use href="#icon-spinner"></use>
      </svg>
      <span class="w-sr-only">Loading</span>
    </div>
  `;
  const validAvailableResponse = `{ "is_valid": true, "is_available": true }`;
  const invalidAvailableResponse = `{ "is_valid": false, "is_available": true }`;
  const unavailableResponse = `{ "is_valid": false, "is_available": false }`;

  const refreshButton = /* html */ `
    <button
      type="button"
      class="button button-small button-secondary button-longrunning button--icon"
      data-controller="w-progress"
      data-action="click->w-preview#setPreviewDataWithAlert click->w-progress#activate"
      data-w-progress-active-value="Refreshing…"
      data-w-progress-duration-seconds-value="300"
    >
      <svg class="icon icon-rotate button-longrunning__icon" aria-hidden="true">
        <use href="#icon-rotate"></use>
      </svg>
      <svg class="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner"></use>
      </svg>

      <em data-w-progress-target="label">Refresh</em>
    </button>
  `;

  beforeEach(() => {
    windowSpy = jest.spyOn(global, 'window', 'get');

    document.body.innerHTML = /* html */ `
      <form method="POST" data-edit-form>
        <input type="text" id="id_title" name="title" value="My Page" />
      </form>
      <div data-side-panel="checks">
        <h2 id="side-panel-checks-title">Checks</h2>
      </div>
      <div data-side-panel="preview">
        <h2 id="side-panel-preview-title">Preview</h2>
        <div
          class="w-preview"
          data-controller="w-preview"
          data-w-preview-unavailable-class="w-preview--unavailable"
          data-w-preview-has-errors-class="w-preview--has-errors"
          data-w-preview-selected-size-class="w-preview__size-button--selected"
          data-w-preview-url-value="${url}"
          data-w-preview-auto-update-value="false"
          data-w-preview-auto-update-interval-value="500"
          data-w-preview-w-progress-outlet="[data-controller='w-preview'] [data-controller='w-progress']"
        >
          <label>
            <input
              type="radio"
              name="preview-size"
              value="mobile"
              data-action="w-preview#togglePreviewSize"
              data-w-preview-target="size"
              data-device-width="375"
              data-default-size
              checked
            />
            Preview in mobile size
          </label>
          <label>
            <input
              type="radio"
              name="preview-size"
              value="tablet"
              data-action="w-preview#togglePreviewSize"
              data-w-preview-target="size"
              data-device-width="768"
            />
            Preview in tablet size
          </label>

          <label>
            <input
              type="radio"
              name="preview-size"
              value="desktop"
              data-action="w-preview#togglePreviewSize"
              data-w-preview-target="size"
              data-device-width="1280"
            />
            Preview in desktop size
          </label>

          <a
            href="/admin/pages/1/edit/preview/"
            data-w-preview-target="newTab"
            data-action="w-preview#openPreviewInNewTab"
          >
            Preview in new tab
          </a>

          <!-- refresh button / spinner !-->

          <select
            id="id_preview_mode"
            name="preview_mode"
            data-w-preview-target="mode"
            data-action="w-preview#setPreviewMode"
          >
            <option value="form" selected>Form</option>
            <option value="landing">Landing page</option>
          </select>

          <iframe
            id="preview-iframe"
            title="Preview"
            data-w-preview-target="iframe"
            data-action="load->w-preview#replaceIframe"
          >
          </iframe>
        </div>
      </div>
    `;
  });

  afterEach(() => {
    application.stop();
    jest.clearAllMocks();
    windowSpy.mockRestore();
    localStorage.removeItem('wagtail:preview-panel-device');
  });

  const initializeOpenedPanel = async () => {
    expect(global.fetch).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-preview', PreviewController);
    await Promise.resolve();

    // Should not have fetched the preview URL
    expect(global.fetch).not.toHaveBeenCalled();

    fetch.mockResponseSuccessJSON(validAvailableResponse);

    // Open the side panel
    const sidePanelContainer = document.querySelector(
      '[data-side-panel="preview"]',
    );
    sidePanelContainer.dispatchEvent(new Event('show'));
    await new Promise(requestAnimationFrame);

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    // At this point, there should only be one fetch call (when the panel is opened)
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Simulate the iframe loading
    const newIframe = document.querySelector('iframe:last-of-type');
    const mockScroll = jest.fn();
    newIframe.contentWindow.scroll = mockScroll;
    newIframe.dispatchEvent(new Event('load'));
    expect(mockScroll).toHaveBeenCalled();

    // Clear the fetch call history
    jest.clearAllMocks();
  };

  it('should load the last device size from localStorage', async () => {
    localStorage.setItem('wagtail:preview-panel-device', 'tablet');
    application = Application.start();
    application.register('w-preview', PreviewController);

    const element = document.querySelector('[data-controller="w-preview"]');
    await Promise.resolve();
    const selectedSizeInput = document.querySelector(
      'input[name="preview-size"]:checked',
    );
    expect(selectedSizeInput.value).toEqual('tablet');
    const selectedSizeLabel = selectedSizeInput.labels[0];
    expect(
      selectedSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(true);
  });

  it('should set the device size accordingly when the input changes', async () => {
    application = Application.start();
    application.register('w-preview', PreviewController);

    const element = document.querySelector('[data-controller="w-preview"]');
    await Promise.resolve();

    // Initial size should be mobile, with the localStorage value unset
    const selectedSizeInput = document.querySelector(
      'input[name="preview-size"]:checked',
    );
    const selectedSizeLabel = selectedSizeInput.labels[0];
    expect(selectedSizeInput.value).toEqual('mobile');
    expect(
      selectedSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(true);
    expect(localStorage.getItem('wagtail:preview-panel-device')).toBeNull();

    const desktopSizeInput = document.querySelector(
      'input[name="preview-size"][value="desktop"]',
    );
    desktopSizeInput.click();
    await Promise.resolve();
    const newSizeInput = document.querySelector(
      'input[name="preview-size"]:checked',
    );
    expect(newSizeInput.value).toEqual('desktop');
    const newSizeLabel = newSizeInput.labels[0];
    expect(
      newSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(true);
    expect(localStorage.getItem('wagtail:preview-panel-device')).toEqual(
      'desktop',
    );
    expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
      '1280',
    );
  });

  it('should observe its own size so it can set the preview width accordingly', async () => {
    expect(ResizeObserverMock).not.toHaveBeenCalled();
    expect(resizeObserverMockObserve).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-preview', PreviewController);

    await Promise.resolve();

    const previewPanel = document.querySelector('.w-preview');

    expect(ResizeObserverMock).toHaveBeenCalledWith(expect.any(Function));
    expect(resizeObserverMockObserve).toHaveBeenCalledWith(previewPanel);
  });

  it('should initialize the preview when the side panel is opened', async () => {
    expect(global.fetch).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-preview', PreviewController);
    await Promise.resolve();

    // Should not have fetched the preview URL
    expect(global.fetch).not.toHaveBeenCalled();

    fetch.mockResponseSuccessJSON(validAvailableResponse);

    // Open the side panel
    const sidePanelContainer = document.querySelector(
      '[data-side-panel="preview"]',
    );
    sidePanelContainer.dispatchEvent(new Event('show'));
    await Promise.resolve();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    // Initially, the iframe src should be empty so it doesn't load the preview
    // until after the request is complete
    let iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0].src).toEqual('');

    await Promise.resolve();

    const expectedUrl = `http://localhost${url}?mode=form&in_preview_panel=true`;

    // Should create a new invisible iframe with the correct URL
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(2);
    const oldIframe = iframes[0];
    const newIframe = iframes[1];
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.style.width).toEqual('0px');
    expect(newIframe.style.height).toEqual('0px');
    expect(newIframe.style.opacity).toEqual('0');
    expect(newIframe.style.position).toEqual('absolute');

    // Mock the iframe's scroll method
    newIframe.contentWindow.scroll = jest.fn();

    // Simulate the iframe loading
    await Promise.resolve();
    newIframe.dispatchEvent(new Event('load'));

    // Should remove the old iframe and make the new one visible
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0]).toBe(newIframe);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.getAttribute('style')).toBeNull();
    expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith(
      oldIframe.contentWindow.scrollX,
      oldIframe.contentWindow.scrollY,
    );

    // Should set the device width property to the selected size (the default)
    const element = document.querySelector('[data-controller="w-preview"]');
    expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
      '375',
    );

    // By the end, there should only be one fetch call
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should clear the preview data if the data is invalid on initial load', async () => {
    expect(global.fetch).not.toHaveBeenCalled();

    // Set to a non-default preview size
    localStorage.setItem('wagtail:preview-panel-device', 'desktop');

    application = Application.start();
    application.register('w-preview', PreviewController);
    await Promise.resolve();

    const element = document.querySelector('[data-controller="w-preview"]');
    const selectedSizeInput = document.querySelector(
      'input[name="preview-size"]:checked',
    );
    expect(selectedSizeInput.value).toEqual('desktop');
    const selectedSizeLabel = selectedSizeInput.labels[0];
    expect(
      selectedSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(true);

    // Should not have fetched the preview URL
    expect(global.fetch).not.toHaveBeenCalled();

    fetch.mockResponseSuccessJSON(invalidAvailableResponse);

    // Open the side panel
    const sidePanelContainer = document.querySelector(
      '[data-side-panel="preview"]',
    );
    sidePanelContainer.dispatchEvent(new Event('show'));
    await Promise.resolve();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    fetch.mockResponseSuccessJSON(`{ "success": true }`);

    await Promise.resolve();

    // Should send a request to clear the preview data
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      headers: {
        'X-CSRFToken': 'test-token',
      },
      method: 'DELETE',
    });

    // Initially, the iframe src should be empty so it doesn't load the preview
    // until after the request is complete
    let iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0].src).toEqual('');

    await Promise.resolve();

    const expectedUrl = `http://localhost${url}?mode=form&in_preview_panel=true`;

    // Should create a new invisible iframe with the correct URL
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(2);
    const oldIframe = iframes[0];
    const newIframe = iframes[1];
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.style.width).toEqual('0px');
    expect(newIframe.style.height).toEqual('0px');
    expect(newIframe.style.opacity).toEqual('0');
    expect(newIframe.style.position).toEqual('absolute');

    // Mock the iframe's scroll method
    newIframe.contentWindow.scroll = jest.fn();

    // Simulate the iframe loading
    await Promise.resolve();
    newIframe.dispatchEvent(new Event('load'));

    // Should remove the old iframe and make the new one visible
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0]).toBe(newIframe);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.getAttribute('style')).toBeNull();
    expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith(
      oldIframe.contentWindow.scrollX,
      oldIframe.contentWindow.scrollY,
    );

    // Should set the has-errors class on the controlled element
    expect(element.classList).toContain('w-preview--has-errors');

    // The "selected" preview size button should remain the same (desktop)
    const currentSizeInput = document.querySelector(
      'input[name="preview-size"]:checked',
    );
    expect(currentSizeInput.value).toEqual('desktop');
    const currentSizeLabel = currentSizeInput.labels[0];
    expect(
      currentSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(true);
    const defaultSizeInput = document.querySelector(
      'input[name="preview-size"][data-default-size]',
    );
    expect(defaultSizeInput.value).toEqual('mobile');
    const defaultSizeLabel = defaultSizeInput.labels[0];
    expect(
      defaultSizeLabel.classList.contains('w-preview__size-button--selected'),
    ).toBe(false);

    // However, the actual rendered size should be the default size
    // (This is because the "Preview is unavailable" screen is actually the
    // rendered preview response in the iframe instead of elements directly
    // rendered in the controller's DOM. To ensure the screen is readable and
    // not scaled down, the iframe is set to the default size.)
    expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
      '375',
    );

    // By the end, there should only be two fetch calls: one to send the invalid
    // preview data and one to clear the preview data
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('should update the preview data when opening in a new tab', async () => {
    await initializeOpenedPanel();
    fetch.mockResponseSuccessJSON(validAvailableResponse);

    // Open the preview in a new tab
    const newTabLink = document.querySelector(
      '[data-w-preview-target="newTab"]',
    );
    newTabLink.click();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    mockWindow({ open: jest.fn() });
    await new Promise(requestAnimationFrame);

    // Should call window.open() with the correct URL, and the base URL should
    // be used as the second argument to ensure the same tab is reused if it's
    // already open even when the URL is different, e.g. when the user changes
    // the preview mode
    expect(window.open).toHaveBeenCalledWith(`http://localhost${url}`, url);
  });

  it('should show an alert if the update request fails when opening in a new tab', async () => {
    await initializeOpenedPanel();
    fetch.mockResponseFailure();

    // Open the preview in a new tab
    const newTabLink = document.querySelector(
      '[data-w-preview-target="newTab"]',
    );
    newTabLink.click();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    mockWindow({ open: jest.fn(), alert: jest.fn() });
    await new Promise(requestAnimationFrame);

    // Should call window.alert() with the correct message
    expect(window.alert).toHaveBeenCalledWith(
      'Error while sending preview data.',
    );

    // Should still open the new tab anyway
    expect(window.open).toHaveBeenCalledWith(`http://localhost${url}`, url);
  });

  it('should only show the spinner after 2s when refreshing the preview', async () => {
    // Mock a 2s successful request
    jest.useFakeTimers();
    fetch.mockResponseSuccessJSON(validAvailableResponse);

    // Add the spinner to the preview panel
    const element = document.querySelector('[data-controller="w-preview"]');
    element.insertAdjacentHTML('beforeend', spinner);
    const spinnerElement = element.querySelector(
      '[data-w-preview-target="spinner"]',
    );

    expect(global.fetch).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-preview', PreviewController);
    await Promise.resolve();

    // Should not have fetched the preview URL
    expect(global.fetch).not.toHaveBeenCalled();

    fetch.mockResponseSuccessJSON(validAvailableResponse);

    // Open the side panel
    const sidePanelContainer = document.querySelector(
      '[data-side-panel="preview"]',
    );
    sidePanelContainer.dispatchEvent(new Event('show'));
    await Promise.resolve();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith('/admin/pages/1/edit/preview/', {
      body: expect.any(Object),
      method: 'POST',
    });

    // Initially, the iframe src should be empty so it doesn't load the preview
    // until after the request is complete
    let iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0].src).toEqual('');

    // Should show the spinner after 2s
    expect(spinnerElement.hidden).toBe(true);
    jest.advanceTimersByTime(2000);
    await Promise.resolve();
    expect(spinnerElement.hidden).toBe(false);
    await Promise.resolve();

    const expectedUrl = `http://localhost${url}?mode=form&in_preview_panel=true`;

    // Should create a new invisible iframe with the correct URL
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(2);
    const oldIframe = iframes[0];
    const newIframe = iframes[1];
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.style.width).toEqual('0px');
    expect(newIframe.style.height).toEqual('0px');
    expect(newIframe.style.opacity).toEqual('0');
    expect(newIframe.style.position).toEqual('absolute');
    // The spinner should still be visible while the iframe is loading
    expect(spinnerElement.hidden).toBe(false);

    // Mock the iframe's scroll method
    newIframe.contentWindow.scroll = jest.fn();

    // Simulate the iframe loading
    await Promise.resolve();
    newIframe.dispatchEvent(new Event('load'));

    // Should remove the old iframe and make the new one visible
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0]).toBe(newIframe);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.getAttribute('style')).toBeNull();
    expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith(
      oldIframe.contentWindow.scrollX,
      oldIframe.contentWindow.scrollY,
    );
    // The spinner should be hidden after the iframe loads
    expect(spinnerElement.hidden).toBe(true);

    // Should set the device width property to the selected size (the default)
    expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
      '375',
    );

    // By the end, there should only be one fetch call
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});
