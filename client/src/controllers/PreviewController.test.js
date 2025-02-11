import { Application } from '@hotwired/stimulus';
import { ProgressController } from './ProgressController';
import { PreviewController } from './PreviewController';

jest.useFakeTimers();
jest.spyOn(global, 'setTimeout');

describe('PreviewController', () => {
  let application;
  let windowSpy;

  const identifier = 'w-preview';

  const events = {
    update: [],
    json: [],
    error: [],
    load: [],
    loaded: [],
    ready: [],
    updated: [],
  };

  const pushEvent = (event) =>
    events[event.type.substring(identifier.length + 1)].push(event);

  const originalWindow = { ...window };
  const mockWindow = (props) =>
    windowSpy.mockImplementation(() => ({
      ...originalWindow,
      ...props,
    }));

  const ResizeObserverMock = jest.fn((callback) => {
    const observed = [];
    return {
      callback,
      observe: jest.fn((el) => observed.push(el)),
      unobserve: jest.fn((el) => observed.splice(observed.indexOf(el), 1)),
      disconnect: jest.fn(() => observed.splice(0, observed.length)),
      // Not a real ResizeObserver method, but useful for simulating resize
      notify: jest.fn((entries) => callback(entries)),
    };
  });

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

  const modeSelect = /* html */ `
    <select
      id="id_preview_mode"
      name="preview_mode"
      data-w-preview-target="mode"
      data-action="w-preview#setPreviewMode"
    >
      <option value="form" selected>Form</option>
      <option value="landing">Landing page</option>
    </select>
  `;

  beforeAll(() => {
    Object.keys(events).forEach((name) => {
      document.addEventListener(`${identifier}:${name}`, pushEvent);
    });
  });

  afterAll(() => {
    Object.keys(events).forEach((name) => {
      document.removeEventListener(`${identifier}:${name}`, pushEvent);
    });
  });

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
          data-w-preview-has-errors-class="w-preview--has-errors"
          data-w-preview-proxy-class="w-preview__proxy"
          data-w-preview-selected-size-class="w-preview__size-button--selected"
          data-w-preview-url-value="${url}"
          data-w-preview-auto-update-interval-value="0"
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
            data-action="w-preview#openPreviewInNewTab:prevent"
          >
            Preview in new tab
          </a>

          <!-- refresh button / spinner !-->

          <!-- preview mode select -->

          <iframe
            id="w-preview-iframe"
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
    jest.clearAllTimers();
    windowSpy.mockRestore();
    localStorage.removeItem('wagtail:preview-panel-device');
    Object.keys(events).forEach((name) => {
      events[name] = [];
    });
  });

  const expectIframeReloaded = async (
    expectedUrl = `http://localhost${url}?in_preview_panel=true`,
  ) => {
    // Should create a new invisible iframe with the correct URL
    let iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(2);
    const oldIframe = iframes[0];
    const newIframe = iframes[1];
    const oldIframeId = oldIframe.id;
    expect(oldIframeId).toBeTruthy();
    expect(newIframe.hasAttribute('id')).toBe(false);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);

    // Pretend the old iframe has scrolled
    oldIframe.contentWindow.scrollX = 200;
    oldIframe.contentWindow.scrollY = 100;

    // Simulate the iframe loading
    const mockScroll = jest.fn();
    newIframe.contentWindow.scroll = mockScroll;
    await Promise.resolve();
    newIframe.dispatchEvent(new Event('load'));
    expect(mockScroll).toHaveBeenCalled();
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0]).toBe(newIframe);
    expect(newIframe.id).toEqual(oldIframeId);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.getAttribute('style')).toBeNull();
    expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
      top: oldIframe.contentWindow.scrollY,
      left: oldIframe.contentWindow.scrollX,
      behavior: 'instant',
    });

    // Clear the fetch call history
    fetch.mockClear();
  };

  const initializeOpenedPanel = async (expectedUrl) => {
    expect(global.fetch).not.toHaveBeenCalled();
    expect(events).toMatchObject({
      update: [],
      json: [],
      error: [],
      load: [],
      loaded: [],
      ready: [],
      updated: [],
    });

    application = Application.start();
    application.register(identifier, PreviewController);
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

    // There's no spinner, so setTimeout should not be called
    expect(setTimeout).not.toHaveBeenCalled();

    // Should send the preview data to the preview URL
    expect(global.fetch).toHaveBeenCalledWith(url, {
      body: expect.any(Object),
      method: 'POST',
    });

    // At this point, there should only be one fetch call (when the panel is opened)
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Initially, the iframe src should be empty so it doesn't load the preview
    // until after the request is complete
    const iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0].src).toEqual('');

    // Simulate the request completing
    await Promise.resolve();

    await expectIframeReloaded(expectedUrl);
    expect(events).toMatchObject({
      update: [expect.any(Event)],
      json: [expect.any(Event)],
      error: [],
      load: [expect.any(Event)],
      loaded: [expect.any(Event)],
      ready: [expect.any(Event)],
      updated: [expect.any(Event)],
    });
  };

  describe('controlling the preview size', () => {
    it('should load the last device size from localStorage', async () => {
      localStorage.setItem('wagtail:preview-panel-device', 'tablet');
      application = Application.start();
      application.register(identifier, PreviewController);

      const element = document.querySelector('[data-controller="w-preview"]');
      await Promise.resolve();
      const selectedSizeInput = document.querySelector(
        'input[name="preview-size"]:checked',
      );
      expect(selectedSizeInput.value).toEqual('tablet');
      const selectedSizeLabel = selectedSizeInput.labels[0];
      expect(
        selectedSizeLabel.classList.contains(
          'w-preview__size-button--selected',
        ),
      ).toBe(true);
    });

    it('should set the device size accordingly when the input changes', async () => {
      application = Application.start();
      application.register(identifier, PreviewController);

      const element = document.querySelector('[data-controller="w-preview"]');
      await Promise.resolve();

      // Initial size should be mobile, with the localStorage value unset
      const selectedSizeInput = document.querySelector(
        'input[name="preview-size"]:checked',
      );
      const selectedSizeLabel = selectedSizeInput.labels[0];
      expect(selectedSizeInput.value).toEqual('mobile');
      expect(
        selectedSizeLabel.classList.contains(
          'w-preview__size-button--selected',
        ),
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

      application = Application.start();
      application.register(identifier, PreviewController);

      await Promise.resolve();

      const previewPanel = document.querySelector('.w-preview');

      expect(ResizeObserverMock).toHaveBeenCalledTimes(1);
      expect(ResizeObserverMock).toHaveBeenCalledWith(expect.any(Function));

      const observer = ResizeObserverMock.mock.results[0].value;
      expect(observer.observe).toHaveBeenCalledWith(previewPanel);

      observer.notify([{ contentRect: { width: 5463 } }]);
      expect(previewPanel.style.getPropertyValue('--preview-panel-width')).toBe(
        '5463',
      );
    });
  });

  describe('basic behavior', () => {
    it('should initialize the preview when the side panel is opened', async () => {
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.ready).toHaveLength(0);

      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      // Should not have fetched the preview URL
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(0);

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Open the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('show'));
      await Promise.resolve();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(events.update).toHaveLength(1);
      expect(events.json).toHaveLength(0);
      expect(events.load).toHaveLength(0);

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');

      await Promise.resolve();
      expect(events.json).toHaveLength(1);
      expect(events.load).toHaveLength(1);

      const expectedUrl = `http://localhost${url}?in_preview_panel=true`;

      // Should create a new invisible iframe with the correct URL
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(2);
      const oldIframe = iframes[0];
      const newIframe = iframes[1];
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);

      // Mock the iframe's scroll method
      newIframe.contentWindow.scroll = jest.fn();

      await Promise.resolve();
      expect(events.loaded).toHaveLength(0);
      expect(events.ready).toHaveLength(0);
      expect(events.updated).toHaveLength(0);

      // Simulate the iframe loading
      newIframe.dispatchEvent(new Event('load'));

      // Should remove the old iframe and make the new one visible
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0]).toBe(newIframe);
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.getAttribute('style')).toBeNull();
      expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: oldIframe.contentWindow.scrollY,
        left: oldIframe.contentWindow.scrollX,
        behavior: 'instant',
      });

      // Should set the device width property to the selected size (the default)
      const element = document.querySelector('[data-controller="w-preview"]');
      expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
        '375',
      );

      // By the end, there should only be one fetch call
      expect(global.fetch).toHaveBeenCalledTimes(1);

      expect(events).toMatchObject({
        update: [expect.any(Event)],
        json: [expect.any(Event)],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });
    });

    it('should not clear the preview data if the data is invalid and unavailable on initial load', async () => {
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.ready).toHaveLength(0);

      // Set to a non-default preview size
      localStorage.setItem('wagtail:preview-panel-device', 'desktop');

      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      const element = document.querySelector('[data-controller="w-preview"]');
      const selectedSizeInput = document.querySelector(
        'input[name="preview-size"]:checked',
      );
      expect(selectedSizeInput.value).toEqual('desktop');
      const selectedSizeLabel = selectedSizeInput.labels[0];
      expect(
        selectedSizeLabel.classList.contains(
          'w-preview__size-button--selected',
        ),
      ).toBe(true);

      // Should not have fetched the preview URL
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(0);

      // Mock invalid data but no stale preview available
      fetch.mockResponseSuccessJSON(unavailableResponse);

      // Open the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('show'));
      await Promise.resolve();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(events.update).toHaveLength(1);
      expect(events.json).toHaveLength(0);

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');
      expect(events.load).toHaveLength(0);

      // Simulate the POST request completing with unavailableResponse
      await Promise.resolve();
      expect(events.json).toHaveLength(1);

      await Promise.resolve();

      // Should NOT send a request to clear the preview data, as there is no
      // stale data that needs to be cleared
      expect(global.fetch).not.toHaveBeenCalledWith(url, {
        headers: { 'x-xsrf-token': 'potato' },
        method: 'DELETE',
      });

      // Should now try to reload the iframe
      expect(events.load).toHaveLength(1);

      const expectedUrl = `http://localhost${url}?in_preview_panel=true`;

      // Should create a new invisible iframe with the correct URL
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(2);
      const oldIframe = iframes[0];
      const newIframe = iframes[1];
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);
      expect(events.ready).toHaveLength(0);

      // Mock the iframe's scroll method
      newIframe.contentWindow.scroll = jest.fn();

      await Promise.resolve();
      expect(events.loaded).toHaveLength(0);
      expect(events.ready).toHaveLength(0);
      expect(events.updated).toHaveLength(0);

      // Simulate the iframe loading
      newIframe.dispatchEvent(new Event('load'));

      // Should remove the old iframe and make the new one visible
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0]).toBe(newIframe);
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.getAttribute('style')).toBeNull();
      expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: oldIframe.contentWindow.scrollY,
        left: oldIframe.contentWindow.scrollX,
        behavior: 'instant',
      });

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
      expect(
        document.querySelectorAll('.w-preview__size-button--selected'),
      ).toHaveLength(1);

      // However, the actual rendered size should be the default size
      // (This is because the "Preview is unavailable" screen is actually the
      // rendered preview response in the iframe instead of elements directly
      // rendered in the controller's DOM. To ensure the screen is readable and
      // not scaled down, the iframe is set to the default size.)
      expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
        '375',
      );

      // By the end, there should only be one fetch call: one to send the initial invalid
      // preview data. No fetch calls to clear the preview data should have been made,
      // as there was no stale data to clear.
      expect(global.fetch).toHaveBeenCalledTimes(1);

      expect(events).toMatchObject({
        update: [expect.any(Event)],
        json: [
          // Initial is invalid but there is an existing preview available,
          // so it should be cleared
          expect.objectContaining({
            detail: { data: { is_valid: false, is_available: false } },
          }),
        ],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });
    });

    it('should clear the preview data if the data is invalid but available on initial load', async () => {
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.ready).toHaveLength(0);

      // Set to a non-default preview size
      localStorage.setItem('wagtail:preview-panel-device', 'desktop');

      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      const element = document.querySelector('[data-controller="w-preview"]');
      const selectedSizeInput = document.querySelector(
        'input[name="preview-size"]:checked',
      );
      expect(selectedSizeInput.value).toEqual('desktop');
      const selectedSizeLabel = selectedSizeInput.labels[0];
      expect(
        selectedSizeLabel.classList.contains(
          'w-preview__size-button--selected',
        ),
      ).toBe(true);

      // Should not have fetched the preview URL
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(0);

      // Mock stale preview data
      fetch.mockResponseSuccessJSON(invalidAvailableResponse);

      // Open the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('show'));
      await Promise.resolve();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(events.update).toHaveLength(1);
      expect(events.json).toHaveLength(0);

      // Mock successful response to clear the preview data
      fetch.mockResponseSuccessJSON(`{ "success": true }`);

      // Simulate the POST request completing with invalidAvailableResponse,
      // which will kick off a DELETE request immediately to clear the stale data
      await Promise.resolve();
      expect(events.json).toHaveLength(1);

      // Should send a request to clear the preview data
      expect(global.fetch).toHaveBeenCalledWith(url, {
        headers: { 'x-xsrf-token': 'potato' },
        method: 'DELETE',
      });
      // Should not try to reload the iframe yet
      expect(events.load).toHaveLength(0);

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');

      // Simulate the DELETE request completing
      await Promise.resolve();
      expect(events.load).toHaveLength(1);

      const expectedUrl = `http://localhost${url}?in_preview_panel=true`;

      // Should create a new invisible iframe with the correct URL
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(2);
      const oldIframe = iframes[0];
      const newIframe = iframes[1];
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);
      expect(events.ready).toHaveLength(0);

      // Mock the iframe's scroll method
      newIframe.contentWindow.scroll = jest.fn();

      await Promise.resolve();
      expect(events.loaded).toHaveLength(0);
      expect(events.ready).toHaveLength(0);
      expect(events.updated).toHaveLength(0);

      // Simulate the iframe loading
      newIframe.dispatchEvent(new Event('load'));

      // Should remove the old iframe and make the new one visible
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0]).toBe(newIframe);
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.getAttribute('style')).toBeNull();
      expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: oldIframe.contentWindow.scrollY,
        left: oldIframe.contentWindow.scrollX,
        behavior: 'instant',
      });

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
      expect(
        document.querySelectorAll('.w-preview__size-button--selected'),
      ).toHaveLength(1);

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

      expect(events).toMatchObject({
        update: [expect.any(Event)],
        json: [
          // Initial is invalid but there is an existing preview available,
          // so it should be cleared
          expect.objectContaining({
            detail: { data: { is_valid: false, is_available: true } },
          }),
        ],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });
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
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      mockWindow({ open: jest.fn() });
      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should call window.open() with the correct URL, and the base URL should
      // be used as the second argument to ensure the same tab is reused if it's
      // already open even when the URL is different, e.g. when the user changes
      // the preview mode
      const absoluteUrl = `http://localhost${url}`;
      expect(window.open).toHaveBeenCalledWith(absoluteUrl, absoluteUrl);
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
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(events.update).toHaveLength(2);

      mockWindow({ open: jest.fn(), alert: jest.fn() });
      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should call window.alert() with the correct message
      expect(window.alert).toHaveBeenCalledWith(
        'Error while sending preview data.',
      );

      // Should still open the new tab anyway
      const absoluteUrl = `http://localhost${url}`;
      expect(window.open).toHaveBeenCalledWith(absoluteUrl, absoluteUrl);

      expect(events).toMatchObject({
        update: [expect.any(Event), expect.any(Event)], // Initial, error
        json: [expect.any(Event)], // Initial
        error: [
          // Error
          expect.objectContaining({ detail: { error: expect.any(Error) } }),
        ],
        load: [expect.any(Event)], // Initial
        loaded: [expect.any(Event)], // Initial
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event)], // Initial, error
      });
    });

    it('should only show the spinner after 2s when refreshing the preview', async () => {
      // Add the spinner to the preview panel
      const element = document.querySelector('[data-controller="w-preview"]');
      element.insertAdjacentHTML('beforeend', spinner);
      const spinnerElement = element.querySelector(
        '[data-w-preview-target="spinner"]',
      );

      expect(global.fetch).not.toHaveBeenCalled();

      application = Application.start();
      application.register(identifier, PreviewController);
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

      // Should set the timeout for the spinner to appear after 2s
      expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 2000);

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');

      // Should not show the spinner initially
      expect(spinnerElement.hidden).toBe(true);

      // Mock a 2s successful request
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      // Should show the spinner after 2s
      expect(spinnerElement.hidden).toBe(false);
      await Promise.resolve();

      const expectedUrl = `http://localhost${url}?in_preview_panel=true`;

      // Should create a new invisible iframe with the correct URL
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(2);
      const oldIframe = iframes[0];
      const newIframe = iframes[1];
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);
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
      expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: oldIframe.contentWindow.scrollY,
        left: oldIframe.contentWindow.scrollX,
        behavior: 'instant',
      });
      // The spinner should be hidden after the iframe loads
      expect(spinnerElement.hidden).toBe(true);

      // Should set the device width property to the selected size (the default)
      expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
        '375',
      );

      // By the end, there should only be one fetch call
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should assume the first device size is the default if none are marked as default', async () => {
      // Remove the default size marker
      document.querySelector(':checked').removeAttribute('checked');
      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      const element = document.querySelector('[data-controller="w-preview"]');

      // Move the tablet size to the first position
      const tabletSize = document.querySelector(
        'label:has(input[name="preview-size"][value="tablet"])',
      );
      element.prepend(tabletSize);

      await initializeOpenedPanel();
      const tabletInput = tabletSize.querySelector('input');
      expect(tabletInput.checked).toBe(true);
      expect(
        tabletSize.classList.contains('w-preview__size-button--selected'),
      ).toBe(true);
    });

    it('should clean up event listeners on disconnect', async () => {
      await initializeOpenedPanel();

      const element = document.querySelector('[data-controller="w-preview"]');
      const controller = application.getControllerForElementAndIdentifier(
        element,
        identifier,
      );
      jest.spyOn(element.parentElement, 'removeEventListener');

      element.removeAttribute('data-controller');
      await Promise.resolve();

      expect(element.parentElement.removeEventListener).toHaveBeenCalledWith(
        'show',
        controller.activatePreview,
      );
      expect(element.parentElement.removeEventListener).toHaveBeenCalledWith(
        'hide',
        controller.deactivatePreview,
      );
    });

    it('should require the url value to be set', async () => {
      const element = document.querySelector('[data-controller="w-preview"]');
      const handleError = jest.fn();
      element.removeAttribute('data-w-preview-url-value');

      application = Application.start();
      application.handleError = handleError;
      application.register(identifier, PreviewController);
      await Promise.resolve();

      expect(handleError).toHaveBeenCalledWith(
        expect.objectContaining({
          message:
            'The preview panel controller requires the data-w-preview-url-value attribute to be set',
        }),
        'Error connecting controller',
        expect.objectContaining({ identifier }),
      );
    });

    it('should not immediately dispatch the loaded event if the iframe src is empty', async () => {
      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      // Simulate Firefox's behavior where the initial iframe without the src
      // attribute immediately dispatches the load event
      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      const iframe = iframes[0];
      iframe.dispatchEvent(new Event('load'));
      await Promise.resolve();

      // Should not dispatch the loaded event, because we haven't actualy loaded
      // the preview yet
      expect(events.loaded).toHaveLength(0);

      // Should not create a new iframe or remove the existing one
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
    });

    it('should not remove the only iframe if the load event is fired', async () => {
      await initializeOpenedPanel();

      let iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      const iframe = iframes[0];

      // Simulate changing the iframe src, which will reload the iframe
      iframe.setAttribute('src', iframe.src + '&test=1');
      await Promise.resolve();
      iframe.contentWindow.scroll = jest.fn();
      iframe.dispatchEvent(new Event('load'));
      await Promise.resolve();

      // Should dispatch the loaded event
      expect(events.loaded).toHaveLength(2);

      // Should not create a new iframe or remove the existing one
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
    });
  });

  describe('auto update cycle from opening the panel with a valid form -> invalid form -> valid form -> closing the panel', () => {
    it('should behave correctly', async () => {
      expect(events.ready).toHaveLength(0);
      const element = document.querySelector('[data-controller="w-preview"]');
      element.setAttribute('data-w-preview-auto-update-interval-value', '500');
      await initializeOpenedPanel();

      // If there are no changes, should not send any request to update the preview
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(1); // Only contains the initial fetch

      // Simulate an invalid form submission
      const input = document.querySelector('input[name="title"');
      input.value = '';
      fetch.mockResponseSuccessJSON(invalidAvailableResponse);

      // After 1s (500ms for check interval, 500ms for request debounce),
      // should send the preview data to the preview URL
      await jest.advanceTimersByTime(1000);
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(2);

      // Should not yet have the has-errors class on the controlled element
      expect(element.classList).not.toContain('w-preview--has-errors');

      // Simulate the request completing
      await Promise.resolve();
      expect(events.json).toHaveLength(2);

      // Should set the has-errors class on the controlled element
      expect(element.classList).toContain('w-preview--has-errors');

      // Should not create a new iframe for reloading the preview
      const iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      // Should not dispatch a load event (only the initial load event exists)
      expect(events.load).toHaveLength(1);

      fetch.mockClear();

      // If there are no changes, should not send any request to update the preview
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();

      // Simulate a change in the form
      input.value = 'New title';

      // After 800ms, the check interval should be triggered but the request
      // should not be fired yet to wait for the debounce
      await jest.advanceTimersByTime(800);
      expect(global.fetch).not.toHaveBeenCalled();

      // Simulate another change (that is valid) in the form
      input.value = 'New title version two';

      // After 400ms (>1s since the first change), the request should still not
      // be sent due to the debounce
      await jest.advanceTimersByTime(400);
      expect(global.fetch).not.toHaveBeenCalled();

      // If we wait another 300ms, the request should be sent as it has been
      // 500ms since the last change
      fetch.mockResponseSuccessJSON(validAvailableResponse);
      await jest.advanceTimersByTime(300);
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(3);

      // Simulate the request completing
      expect(events.json).toHaveLength(2);
      expect(events.load).toHaveLength(1);
      await Promise.resolve();
      expect(events.json).toHaveLength(3);
      expect(events.load).toHaveLength(2);

      // Should no longer have the has-errors class on the controlled element
      expect(element.classList).not.toContain('w-preview--has-errors');

      // Expect the iframe to be reloaded
      expect(events.loaded).toHaveLength(1);
      await expectIframeReloaded();
      expect(events.loaded).toHaveLength(2);

      // Close the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('hide'));
      await Promise.resolve();

      // Any further changes should not trigger the auto update
      input.value = 'Changes should be ignored';
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();

      expect(events).toMatchObject({
        // Initial, invalid, valid
        update: [expect.any(Event), expect.any(Event), expect.any(Event)],
        json: [
          expect.objectContaining({
            detail: { data: { is_valid: true, is_available: true } },
          }),
          expect.objectContaining({
            detail: { data: { is_valid: false, is_available: true } },
          }),
          expect.objectContaining({
            detail: { data: { is_valid: true, is_available: true } },
          }),
        ],
        error: [],
        // Initial, valid (the invalid form submission does not reload the iframe)
        load: [expect.any(Event), expect.any(Event)],
        loaded: [expect.any(Event), expect.any(Event)],
        ready: [expect.any(Event)],
        // Initial, invalid, valid
        updated: [expect.any(Event), expect.any(Event), expect.any(Event)],
      });
    });
  });

  describe('manual update using a button', () => {
    let refreshButtonElement;

    beforeEach(async () => {
      await initializeOpenedPanel();
      application.register('w-progress', ProgressController);

      // Add the refresh button to the preview panel
      const element = document.querySelector('[data-controller="w-preview"]');
      element.insertAdjacentHTML('beforeend', refreshButton);
      refreshButtonElement = element.querySelector(
        '[data-controller="w-progress"]',
      );
    });

    it('should update the preview when the button is clicked', async () => {
      const input = document.querySelector('input[name="title"');
      input.value = 'Changes should not trigger anything';

      // Should not send any request to update the preview
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Simulate a click on the refresh button
      refreshButtonElement.click();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      jest.advanceTimersByTime(1);
      await Promise.resolve();

      expect(refreshButtonElement.disabled).toBe(true);

      // Simulate the request completing
      await Promise.resolve();

      // Should create a new iframe for reloading the preview
      await expectIframeReloaded();

      expect(refreshButtonElement.disabled).toBe(false);

      jest.clearAllMocks();

      // Close the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('hide'));
      await Promise.resolve();

      // Any further changes should also not trigger the auto update
      input.value = 'Changes should never trigger an update';
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should show an alert if the request fails when clicking the refresh button', async () => {
      const input = document.querySelector('input[name="title"');
      input.value = 'Changes should not trigger anything';

      // Should not send any request to update the preview
      await jest.advanceTimersByTime(10000);
      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseFailure();

      // Simulate a click on the refresh button
      refreshButtonElement.click();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      mockWindow({ open: jest.fn(), alert: jest.fn() });
      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should call window.alert() with the correct message
      expect(window.alert).toHaveBeenCalledWith(
        'Error while sending preview data.',
      );
    });
  });

  describe('switching between different preview modes', () => {
    let previewModeElement;

    beforeEach(async () => {
      // Add the preview mode selector to the preview panel
      const element = document.querySelector('[data-controller="w-preview"]');
      element.insertAdjacentHTML('beforeend', modeSelect);
      previewModeElement = element.querySelector(
        '[data-w-preview-target="mode"]',
      );

      await initializeOpenedPanel(
        `http://localhost${url}?mode=form&in_preview_panel=true`,
      );
    });

    it('should update the preview with the correct URL when switching to a different mode', async () => {
      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Simulate changing the preview mode
      previewModeElement.value = 'landing';
      previewModeElement.dispatchEvent(new Event('change'));
      await Promise.resolve();

      // Should immediately send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      // Simulate the request completing
      await Promise.resolve();

      // Should create a new iframe for reloading the preview using the new URL
      // with the correct mode query parameter
      await expectIframeReloaded(
        `http://localhost${url}?mode=landing&in_preview_panel=true`,
      );

      jest.clearAllMocks();
    });

    it('should show an alert if the request fails when changing the preview mode', async () => {
      fetch.mockResponseFailure();

      // Simulate changing the preview mode
      previewModeElement.value = 'landing';
      previewModeElement.dispatchEvent(new Event('change'));

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      mockWindow({ open: jest.fn(), alert: jest.fn() });
      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should call window.alert() with the correct message
      expect(window.alert).toHaveBeenCalledWith(
        'Error while sending preview data.',
      );
    });
  });

  describe('using different URLs for sending vs rendering the preview data', () => {
    beforeEach(() => {
      // Add the render URL value to the preview controller
      const element = document.querySelector('[data-controller="w-preview"]');
      element.setAttribute(
        'data-w-preview-render-url-value',
        'https://app.example.com/preview/foo/7/',
      );
    });

    it('should send the preview data to the urlValue and the render should load with renderUrlValue', async () => {
      await initializeOpenedPanel(
        `https://app.example.com/preview/foo/7/?in_preview_panel=true`,
      );

      // Should also make sure the new tab link uses the render URL value
      // (without the in_preview_panel param)
      const newTabLink = document.querySelector(
        '[data-w-preview-target="newTab"]',
      );
      expect(newTabLink.href).toEqual('https://app.example.com/preview/foo/7/');
    });

    it('should also set the preview mode query param on the render URL if the mode selector exists', async () => {
      const element = document.querySelector('[data-controller="w-preview"]');
      element.insertAdjacentHTML('beforeend', modeSelect);
      await initializeOpenedPanel(
        `https://app.example.com/preview/foo/7/?mode=form&in_preview_panel=true`,
      );

      // Should also make sure the new tab link uses the render URL value
      // (with the mode param but without the in_preview_panel param)
      const newTabLink = document.querySelector(
        '[data-w-preview-target="newTab"]',
      );
      expect(newTabLink.href).toEqual(
        'https://app.example.com/preview/foo/7/?mode=form',
      );
    });
  });

  describe('cancelling specific parts of the process using events', () => {
    let refreshButtonElement;

    beforeEach(async () => {
      await initializeOpenedPanel();
      application.register('w-progress', ProgressController);

      // Add the refresh button to the preview panel to ease testing
      const element = document.querySelector('[data-controller="w-preview"]');
      element.insertAdjacentHTML('beforeend', refreshButton);
      refreshButtonElement = element.querySelector(
        '[data-controller="w-progress"]',
      );
    });

    it('should allow an entire update request to be cancelled', async () => {
      document.addEventListener(
        'w-preview:update',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Simulate a click on the refresh button
      refreshButtonElement.click();

      await jest.runAllTimersAsync();

      // Should not send the preview data to the preview URL
      expect(global.fetch).not.toHaveBeenCalled();

      // Should have an additional update event, but the rest stay the same
      // as after the initial load
      expect(events).toMatchObject({
        update: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
        ],
        json: [expect.any(Event)],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });

      refreshButtonElement.click();

      await jest.runAllTimersAsync();

      // Should update the preview, as the event listener is only called once
      // and at this point we're waiting for the iframe to load
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events).toMatchObject({
        update: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
          expect.objectContaining({ defaultPrevented: false }),
        ],
        json: [expect.any(Event), expect.any(Event)],
        error: [],
        load: [expect.any(Event), expect.any(Event)],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });

      await expectIframeReloaded();
      expect(events).toMatchObject({
        update: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
          expect.objectContaining({ defaultPrevented: false }),
        ],
        json: [expect.any(Event), expect.any(Event)],
        error: [],
        load: [expect.any(Event), expect.any(Event)],
        loaded: [expect.any(Event), expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event)],
      });
    });

    it('should allow only the iframe reload to be cancelled', async () => {
      document.addEventListener(
        'w-preview:load',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Simulate a click on the refresh button
      refreshButtonElement.click();

      await jest.runAllTimersAsync();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Should have additional events like a regular update, except the loaded
      // event as the iframe load was cancelled by the load event listener.
      // The updated event should still be dispatched to indicate that the
      // process has finished.
      expect(events).toMatchObject({
        update: [expect.any(Event), expect.any(Event)],
        json: [expect.any(Event), expect.any(Event)],
        error: [],
        load: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
        ],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event)],
      });

      // Should not create a new iframe for reloading the preview
      const iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      refreshButtonElement.click();

      await jest.runAllTimersAsync();

      // Should update the preview and reload the iframe, as the event listener
      // is only called once and at this point we're waiting for the iframe to load
      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(events).toMatchObject({
        update: [expect.any(Event), expect.any(Event), expect.any(Event)],
        json: [expect.any(Event), expect.any(Event), expect.any(Event)],
        error: [],
        load: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
          expect.objectContaining({ defaultPrevented: false }),
        ],
        loaded: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event)],
      });

      await expectIframeReloaded();
      expect(events).toMatchObject({
        update: [expect.any(Event), expect.any(Event), expect.any(Event)],
        json: [expect.any(Event), expect.any(Event), expect.any(Event)],
        error: [],
        load: [
          expect.any(Event),
          expect.objectContaining({ defaultPrevented: true }),
          expect.objectContaining({ defaultPrevented: false }),
        ],
        loaded: [expect.any(Event), expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event), expect.any(Event)],
      });
    });
  });
});
