import { Application } from '@hotwired/stimulus';
import axe from 'axe-core';
import { ProgressController } from './ProgressController';
import { PreviewController } from './PreviewController';
import { wagtailPreviewPlugin } from '../includes/previewPlugin';
import { UnsavedController } from './UnsavedController';

jest.mock('axe-core', () => {
  const originalAxe = jest.requireActual('axe-core');
  return {
    ...originalAxe,
    run: jest.fn(),
    utils: {
      ...originalAxe.utils,
      sendCommandToFrame: jest.fn(),
    },
  };
});

jest.useFakeTimers();
jest.spyOn(global, 'setTimeout');

describe('PreviewController', () => {
  let application;
  let windowSpy;
  let mockScroll;
  let mockOldIframeLocation;
  let mockNewIframeLocation;
  let mockA11yResults;
  let mockExtractedContent;

  const identifier = 'w-preview';

  const events = {
    update: [],
    json: [],
    error: [],
    load: [],
    loaded: [],
    content: [],
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

  function mockAxeResults() {
    axe.run.mockResolvedValueOnce(mockA11yResults);
    axe.utils.sendCommandToFrame.mockImplementationOnce(
      (frame, options, callback) => {
        callback(mockExtractedContent);
      },
    );
  }

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

  const axeConfig = {
    context: { include: ['main'] },
    options: {},
    messages: {
      'heading-order': {
        error_name: 'Incorrect heading hierarchy',
        help_text: 'Avoid skipping levels',
      },
    },
    spec: {},
  };

  const checksSidePanel = /* html */ `
    <button type="button" data-side-panel-toggle="checks">
      <div data-side-panel-toggle-counter></div>
    </button>
    <div data-side-panel="checks" hidden>
      <h2 id="side-panel-checks-title">Checks</h2>
      <template id="w-a11y-result-row-template">
        <div data-a11y-result-row>
          <h3>
            <span data-a11y-result-name></span>
          </h3>
          <div data-a11y-result-help></div>
          <button
            data-a11y-result-selector
            type="button"
            aria-label="Show issue"
          >
            <span data-a11y-result-selector-text></span>
          </button>
        </div>
      </template>
      <h3>Word count: <span data-content-word-count>-</span></h3>
      <h3>Reading time: <span data-content-reading-time>-</span></h3>
      <h3>Readability: <span data-content-readability-score>-</span></h3>
      <h3>Issues found: <span data-a11y-result-count>-</span></h3>
      <div data-checks-panel></div>
    </div>
    <script type="application/json" id="accessibility-axe-configuration">
      ${JSON.stringify(axeConfig)}
    </script>
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
    mockScroll = jest.fn();
    mockOldIframeLocation = null;
    mockNewIframeLocation = null;

    document.body.innerHTML = /* html */ `
      <form data-controller="w-unsaved" method="POST" data-edit-form>
        <input type="text" id="id_title" name="title" value="My Page" />
      </form>
      <div data-side-panel="preview" hidden>
        <h2 id="side-panel-preview-title">Preview</h2>
        <div
          class="w-preview"
          data-controller="w-preview"
          data-action="w-unsaved:add@document->w-preview#setStale"
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
    onLoad = jest.fn(),
  ) => {
    // Should create a new invisible iframe with the correct URL
    let iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(2);
    const oldIframe = iframes[0];
    const newIframe = iframes[1];
    const oldIframeId = oldIframe.id;
    const initial = !oldIframe.src;
    expect(oldIframeId).toBeTruthy();
    expect(newIframe.hasAttribute('id')).toBe(false);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.classList.contains('w-preview__proxy')).toBe(true);

    // Pretend the old iframe has scrolled
    oldIframe.contentWindow.scrollX = 200;
    oldIframe.contentWindow.scrollY = 100;

    // Apply location mocks to allow testing cross-origin iframes
    if (mockOldIframeLocation) {
      delete oldIframe.contentWindow.location;
      oldIframe.contentWindow.location = mockOldIframeLocation;
    }
    if (mockNewIframeLocation) {
      delete newIframe.contentWindow.location;
      newIframe.contentWindow.location = mockNewIframeLocation;
    }

    // Simulate the iframe loading
    newIframe.contentWindow.scroll = mockScroll;
    await Promise.resolve();
    newIframe.dispatchEvent(new Event('load'));
    await Promise.resolve();
    await Promise.resolve();
    await onLoad(newIframe);
    iframes = document.querySelectorAll('iframe');
    expect(iframes.length).toEqual(1);
    expect(iframes[0]).toBe(newIframe);
    expect(newIframe.id).toEqual(oldIframeId);
    expect(newIframe.src).toEqual(expectedUrl);
    expect(newIframe.getAttribute('style')).toBeNull();
    if (!initial && !mockOldIframeLocation && !mockNewIframeLocation) {
      expect(mockScroll).toHaveBeenCalled();
      expect(newIframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: oldIframe.contentWindow.scrollY,
        left: oldIframe.contentWindow.scrollX,
        behavior: 'instant',
      });
    } else {
      expect(mockScroll).not.toHaveBeenCalled();
    }

    if (mockA11yResults) {
      // Simulate the userbar's Axe being ready and instructing the controller
      // to run Axe from the parent window.
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { wagtail: { type: 'w-userbar:axe-ready' } },
        }),
      );
    }

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
      content: [],
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
    sidePanelContainer.hidden = false;
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

    // If content checks are enabled, there are a few more promises to resolve
    await jest.runOnlyPendingTimersAsync();

    expect(events).toMatchObject({
      update: [expect.any(Event)],
      json: [expect.any(Event)],
      error: [],
      load: [expect.any(Event)],
      loaded: [expect.any(Event)],
      content: mockExtractedContent ? [expect.any(Event)] : [],
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

    it('should have a fallback width if the input is missing the data attribute', async () => {
      application = Application.start();
      application.register(identifier, PreviewController);

      const element = document.querySelector('[data-controller="w-preview"]');
      await Promise.resolve();

      const tabletSizeInput = document.querySelector(
        'input[name="preview-size"][value="tablet"]',
      );
      tabletSizeInput.removeAttribute('data-device-width');
      tabletSizeInput.click();
      await Promise.resolve();
      const newSizeInput = document.querySelector(
        'input[name="preview-size"]:checked',
      );
      expect(newSizeInput.value).toEqual('tablet');
      const newSizeLabel = newSizeInput.labels[0];
      expect(
        newSizeLabel.classList.contains('w-preview__size-button--selected'),
      ).toBe(true);
      expect(localStorage.getItem('wagtail:preview-panel-device')).toEqual(
        'tablet',
      );
      expect(element.style.getPropertyValue('--preview-device-width')).toEqual(
        PreviewController.fallbackWidth, // 375px
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
        content: [],
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
        content: [],
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
        content: [],
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

    it('should not fire an update request when there is a pending update', async () => {
      await initializeOpenedPanel();
      fetch.mockResponseSuccessJSON(validAvailableResponse);

      // Open the preview in a new tab
      const newTabLink = document.querySelector(
        '[data-w-preview-target="newTab"]',
      );
      newTabLink.click();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      // Click the link again multiple times
      newTabLink.click();
      newTabLink.click();

      mockWindow({ open: jest.fn() });
      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should not send another request to the preview URL
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Should call window.open() with the correct URL, and the base URL should
      // be used as the second argument to ensure the same tab is reused if it's
      // already open even when the URL is different, e.g. when the user changes
      // the preview mode
      const absoluteUrl = `http://localhost${url}`;
      expect(window.open).toHaveBeenCalledTimes(3);
      expect(window.open).toHaveBeenNthCalledWith(1, absoluteUrl, absoluteUrl);
      expect(window.open).toHaveBeenNthCalledWith(2, absoluteUrl, absoluteUrl);
      expect(window.open).toHaveBeenNthCalledWith(3, absoluteUrl, absoluteUrl);
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
        content: [],
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

      // Simulate the iframe loading
      await Promise.resolve();
      newIframe.dispatchEvent(new Event('load'));

      // Should remove the old iframe and make the new one visible
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0]).toBe(newIframe);
      expect(newIframe.src).toEqual(expectedUrl);
      expect(newIframe.getAttribute('style')).toBeNull();
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
        controller.checkAndUpdatePreview,
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
      await jest.runOnlyPendingTimersAsync();

      expect(iframe.contentWindow.scroll).toHaveBeenCalledWith({
        top: iframe.contentWindow.scrollY,
        left: iframe.contentWindow.scrollX,
        behavior: 'instant',
      });

      // Should dispatch the loaded event
      expect(events.loaded).toHaveLength(2);

      // Should not create a new iframe or remove the existing one
      iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
    });

    it('should immediately update the preview if the panel was already open on connect', async () => {
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('show'));
      sidePanelContainer.hidden = false;
      await Promise.resolve();

      expect(global.fetch).not.toHaveBeenCalled();
      expect(events).toMatchObject({
        update: [],
        json: [],
        error: [],
        load: [],
        loaded: [],
        content: [],
        ready: [],
        updated: [],
      });

      // Should not have fetched the preview URL
      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      // There's no spinner, so setTimeout should not be called
      expect(setTimeout).not.toHaveBeenCalled();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      // At this point, there should only be one fetch call (upon connect)
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      const iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');

      // Simulate the request completing
      await Promise.resolve();
      await Promise.resolve();

      await expectIframeReloaded();

      // If content checks are enabled, there are a few more promises to resolve
      await jest.runOnlyPendingTimersAsync();

      expect(events).toMatchObject({
        update: [expect.any(Event)],
        json: [expect.any(Event)],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        content: [],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });
    });
  });

  describe('auto update based on form state', () => {
    beforeEach(async () => {
      await initializeOpenedPanel();
      // Register UnsavedController to detect form changes
      application.register('w-unsaved', UnsavedController);
      // Wait for the initial delay of setting up w-unsaved's initial form data
      await jest.runOnlyPendingTimersAsync();
    });

    it('should behave correctly with auto-update', async () => {
      const element = document.querySelector('[data-controller="w-preview"]');
      element.setAttribute('data-w-preview-auto-update-interval-value', '700');

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce before notifying of no further changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for the preview auto update interval
      await jest.runOnlyPendingTimersAsync();
      // If there are no changes, should not send any request to update the preview
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(1); // Only contains the initial fetch

      // Simulate an invalid form submission
      const input = document.querySelector('input[name="title"');
      input.value = '';
      fetch.mockResponseSuccessJSON(invalidAvailableResponse);

      // Trigger the next check interval (>=500ms)
      await jest.advanceTimersByTimeAsync(510);
      // Still hasn't sent any request yet in case further changes are made
      expect(global.fetch).not.toHaveBeenCalled();
      // Trigger another check (>=500ms)
      await jest.advanceTimersByTimeAsync(510);
      // Still hasn't sent any request due to the debounce
      expect(global.fetch).not.toHaveBeenCalled();
      // w-unsaved hasn't notified the change so the stale value is still unset
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');
      // If we wait another 10ms, w-unsaved notifies the change
      // and w-preview now has the stale value attribute set
      await jest.advanceTimersByTimeAsync(10);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('true');
      // The request has not been sent,
      // as we're waiting for the w-preview auto update interval
      expect(global.fetch).not.toHaveBeenCalled();
      // Now we wait for the auto update interval to trigger the request
      await jest.advanceTimersByTimeAsync(700);

      // Now the request should be sent
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(2);

      // Simulate the request completing
      expect(events.json).toHaveLength(2);

      // Should set the has-errors class on the controlled element
      expect(element.classList).toContain('w-preview--has-errors');

      // Should not create a new iframe for reloading the preview
      const iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      // Should not dispatch a load event (only the initial load event exists)
      expect(events.load).toHaveLength(1);

      fetch.mockClear();

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();
      // Wait for the preview auto update interval
      await jest.runOnlyPendingTimersAsync();
      // If there are no changes, should not send any request to update the preview
      expect(global.fetch).not.toHaveBeenCalled();

      // Simulate a change in the form
      input.value = 'New title';

      // After the check interval, the request should not be fired yet to wait
      // for the next check
      await jest.runOnlyPendingTimersAsync();
      expect(global.fetch).not.toHaveBeenCalled();

      // Simulate another change (that is valid) in the form
      input.value = 'New title version two';

      // After the next check interval, the request should still not
      // be sent due to the debounce
      await jest.advanceTimersByTime(510);
      expect(global.fetch).not.toHaveBeenCalled();

      // If we wait for the next timer, the request should be sent as now
      // the w-unsaved controller has notified us of no further changes
      fetch.mockResponseSuccessJSON(validAvailableResponse);
      // Wait for debounce before notifying of no further changes
      await jest.runOnlyPendingTimersAsync();
      // Now we wait for the auto update interval to trigger the request
      await jest.advanceTimersByTimeAsync(700);
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(3);
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
      sidePanelContainer.hidden = true;
      await Promise.resolve();
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();
      // Wait for the preview auto update interval
      await jest.runOnlyPendingTimersAsync();

      // Reopening the side panel should not trigger an update request,
      // as there were no changes since it was closed
      expect(global.fetch).toHaveBeenCalledTimes(0);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');
      sidePanelContainer.dispatchEvent(new Event('show'));
      sidePanelContainer.hidden = false;
      await Promise.resolve();
      expect(global.fetch).toHaveBeenCalledTimes(0);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // Close the side panel again
      sidePanelContainer.dispatchEvent(new Event('hide'));
      sidePanelContainer.hidden = true;
      await Promise.resolve();
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // Any further changes should not trigger the auto update
      input.value = 'Changes should be ignored';
      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();
      // Wait for the preview auto update interval
      await jest.runOnlyPendingTimersAsync();
      // Should not send any request to update the preview
      expect(global.fetch).not.toHaveBeenCalled();
      // The stale value attribute should be set to true, so that when reopening
      // the panel, it knows to send an update immediately
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('true');

      // Reopening the side panel should now trigger an update request,
      // as there were changes since it was closed
      fetch.mockResponseSuccessJSON(validAvailableResponse);
      expect(global.fetch).toHaveBeenCalledTimes(0);
      sidePanelContainer.dispatchEvent(new Event('show'));
      sidePanelContainer.hidden = false;
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(4);
      expect(events.json).toHaveLength(3);
      await Promise.resolve();
      expect(events.json).toHaveLength(4);
      expect(events.load).toHaveLength(3);

      // Expect the iframe to be reloaded
      expect(events.loaded).toHaveLength(2);
      await expectIframeReloaded();
      expect(events.loaded).toHaveLength(3);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // By the end, the events should show the full cycle of updates
      expect(events).toMatchObject({
        // Initial, invalid, valid, valid
        update: [
          expect.any(Event),
          expect.any(Event),
          expect.any(Event),
          expect.any(Event),
        ],
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
          expect.objectContaining({
            detail: { data: { is_valid: true, is_available: true } },
          }),
        ],
        error: [],
        // Initial, valid (the invalid form submission does not reload the iframe), valid
        load: [expect.any(Event), expect.any(Event), expect.any(Event)],
        loaded: [expect.any(Event), expect.any(Event), expect.any(Event)],
        content: [],
        ready: [expect.any(Event)],
        // Initial, invalid, valid, valid
        updated: [
          expect.any(Event),
          expect.any(Event),
          expect.any(Event),
          expect.any(Event),
        ],
      });
    });

    it('should not auto-update when auto-update interval is set to 0', async () => {
      const element = document.querySelector('[data-controller="w-preview"]');
      // The test setup sets the auto-update interval to 0 (disabled)
      expect(
        element.getAttribute('data-w-preview-auto-update-interval-value'),
      ).toBe('0');

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce before notifying of no further changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce of the preview interval setting
      await jest.runOnlyPendingTimersAsync();
      // If there are no changes, should not send any request to update the preview
      expect(global.fetch).not.toHaveBeenCalled();
      expect(events.update).toHaveLength(1); // Only contains the initial fetch

      const input = document.querySelector('input[name="title"');

      // Simulate a change in the form
      input.value = 'New title';

      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');
      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();

      // With the auto-update interval set to 0, should not send any request
      expect(global.fetch).not.toHaveBeenCalled();
      // but the stale value attribute should be set to true
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('true');

      // Close the side panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('hide'));
      sidePanelContainer.hidden = true;
      await Promise.resolve();

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();

      // Should not send any request to update the preview while closed
      expect(global.fetch).not.toHaveBeenCalled();
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('true');

      // Reopening the side panel should now trigger an update request,
      // as there were changes since it was closed
      fetch.mockResponseSuccessJSON(validAvailableResponse);
      sidePanelContainer.dispatchEvent(new Event('show'));
      sidePanelContainer.hidden = false;
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(events.update).toHaveLength(2);
      expect(events.json).toHaveLength(1);
      await Promise.resolve();
      expect(events.json).toHaveLength(2);
      expect(events.load).toHaveLength(2);

      // Expect the iframe to be reloaded
      expect(events.loaded).toHaveLength(1);
      await expectIframeReloaded();
      expect(events.loaded).toHaveLength(2);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      expect(events).toMatchObject({
        // Initial, reopening
        update: [expect.any(Event), expect.any(Event)],
        json: [
          expect.objectContaining({
            detail: { data: { is_valid: true, is_available: true } },
          }),
          expect.objectContaining({
            detail: { data: { is_valid: true, is_available: true } },
          }),
        ],
        error: [],
        // Initial, reopening
        load: [expect.any(Event), expect.any(Event)],
        loaded: [expect.any(Event), expect.any(Event)],
        content: [],
        ready: [expect.any(Event)],
        // Initial, reopening
        updated: [expect.any(Event), expect.any(Event)],
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

    describe('cross-domain iframe behavior', () => {
      let oldIframe;
      let spies;
      // Mock a SecurityError that is raised when accessing
      // iframe.contentWindow.location.origin on a cross-origin frame.
      const crossOriginLocation = {
        get origin() {
          throw new Error(
            'SecurityError: Cannot access properties of a cross-origin frame.',
          );
        },
      };

      beforeEach(async () => {
        // Initialize the preview panel normally
        const element = document.querySelector('[data-controller="w-preview"]');
        element.setAttribute(
          'data-w-preview-auto-update-interval-value',
          '200',
        );
        element.setAttribute(
          'data-w-preview-render-url-value',
          'https://headless.site/$preview/foo/7/',
        );

        await initializeOpenedPanel(
          `https://headless.site/$preview/foo/7/?in_preview_panel=true`,
        );
        // Register UnsavedController to detect form changes and wait for its
        // initial delayed setup
        application.register('w-unsaved', UnsavedController);
        await jest.runOnlyPendingTimersAsync();
        global.fetch.mockClear();
      });

      const setup = async (locationMocks) => {
        mockOldIframeLocation = locationMocks.oldIframe;
        mockNewIframeLocation = locationMocks.newIframe;

        oldIframe = document.querySelector('iframe');

        fetch.mockResponseSuccessJSON(validAvailableResponse);
        const input = document.querySelector('input[name="title"');
        input.value = 'Changed title';

        // Trigger auto update check
        await jest.runOnlyPendingTimersAsync();
        // Wait for debounce before notifying of no further changes
        await jest.runOnlyPendingTimersAsync();
        // Wait for debounce of the preview interval setting
        await jest.runOnlyPendingTimersAsync();

        // Should send the preview data to the backend URL
        expect(global.fetch).toHaveBeenCalledWith(url, {
          body: expect.any(Object),
          method: 'POST',
        });
        expect(global.fetch).toHaveBeenCalledTimes(1);

        spies = [
          jest.spyOn(window, 'addEventListener'),
          jest.spyOn(window, 'removeEventListener'),
          jest.spyOn(oldIframe.contentWindow, 'postMessage'),
        ];
      };

      afterEach(() => {
        spies.forEach((spy) => spy.mockRestore());
      });

      it('should use postMessage to restore the scroll position on the new iframe', async () => {
        // Set up both old and new iframe locations to be cross-origin
        await setup({
          oldIframe: crossOriginLocation,
          newIframe: crossOriginLocation,
        });

        await expectIframeReloaded(
          'https://headless.site/$preview/foo/7/?in_preview_panel=true',
          async (newIframe) => {
            expect(window.addEventListener).toHaveBeenCalledWith(
              'message',
              expect.any(Function),
            );

            jest.spyOn(newIframe.contentWindow, 'postMessage');

            // Unrelated Wagtail message to the parent window should not trigger
            // any postMessage calls to any of the iframes
            window.postMessage(
              { wagtail: { type: 'w-other:unrelated' } },
              'http://localhost',
            );
            await jest.advanceTimersToNextTimerAsync();
            expect(oldIframe.contentWindow.postMessage).not.toHaveBeenCalled();
            expect(newIframe.contentWindow.postMessage).not.toHaveBeenCalled();

            // Simulate the newIframe sending a request to the parent window for
            // the scroll position of the oldIframe
            window.postMessage(
              {
                wagtail: {
                  type: 'w-preview:request-scroll',
                  origin: 'https://headless.site',
                },
              },
              'http://localhost',
            );
            await jest.advanceTimersToNextTimerAsync();

            // Should call postMessage on the oldIframe to get its scroll position
            expect(oldIframe.contentWindow.postMessage).toHaveBeenCalledWith(
              {
                wagtail: { type: 'w-preview:get-scroll-position' },
              },
              'https://headless.site',
            );

            const message = {
              type: 'w-preview:set-scroll-position',
              x: 123,
              y: 456,
              origin: 'https://headless.site',
            };

            // Should not clean up the event listener yet as we're still waiting
            // for the scroll restoration communication to complete
            expect(window.removeEventListener).not.toHaveBeenCalled();

            // Simulate the oldIframe sending its scroll position to the parent window
            window.postMessage({ wagtail: message }, 'http://localhost');
            await jest.advanceTimersToNextTimerAsync();

            // Should call postMessage on the newIframe to set its scroll position
            expect(newIframe.contentWindow.postMessage).toHaveBeenCalledWith(
              { wagtail: message },
              'https://headless.site',
            );

            // Should clean up the event listener as the scroll restoration
            // communication has completed successfully
            expect(window.removeEventListener).toHaveBeenCalledWith(
              'message',
              expect.any(Function),
            );
          },
        );
      });

      it('should have a timeout for the scroll restoration communication', async () => {
        // Set up both old and new iframe locations to be cross-origin
        await setup({
          oldIframe: crossOriginLocation,
          newIframe: crossOriginLocation,
        });

        await expectIframeReloaded(
          'https://headless.site/$preview/foo/7/?in_preview_panel=true',
          async (newIframe) => {
            expect(window.addEventListener).toHaveBeenCalledWith(
              'message',
              expect.any(Function),
            );

            jest.spyOn(newIframe.contentWindow, 'postMessage');

            // Unrelated message (not from Wagtail) to the parent window should
            // not trigger any postMessage calls to any of the iframes
            window.postMessage(
              { someExtension: { says: 'hello' } },
              'http://localhost',
            );
            await jest.advanceTimersToNextTimerAsync();
            expect(oldIframe.contentWindow.postMessage).not.toHaveBeenCalled();
            expect(newIframe.contentWindow.postMessage).not.toHaveBeenCalled();

            // Should not clean up the event listener yet as we're still waiting
            // for the scroll restoration communication to complete
            expect(window.removeEventListener).not.toHaveBeenCalled();

            // After the timeout has passed, the scroll restoration
            // communication should be considered failed and no postMessage
            // should be sent to the newIframe, but the rest of the iframe
            // reload process should continue
            await jest.advanceTimersByTimeAsync(
              PreviewController.scrollRestoreTimeout,
            );
            expect(oldIframe.contentWindow.postMessage).not.toHaveBeenCalled();
            expect(newIframe.contentWindow.postMessage).not.toHaveBeenCalled();

            // Should clean up the event listener as the scroll restoration
            // communication has timed out
            expect(window.removeEventListener).toHaveBeenCalledWith(
              'message',
              expect.any(Function),
            );
          },
        );
      });

      it('should skip scroll restoration if only the old iframe is cross-origin', async () => {
        // Set up only the old iframe location to be cross-origin
        await setup({ oldIframe: crossOriginLocation });

        await expectIframeReloaded(
          'https://headless.site/$preview/foo/7/?in_preview_panel=true',
          async (newIframe) => {
            expect(window.addEventListener).not.toHaveBeenCalled();
            expect(mockScroll).not.toHaveBeenCalled();
          },
        );
      });

      it('should skip scroll restoration if only the new iframe is cross-origin', async () => {
        // Set up only the new iframe location to be cross-origin
        await setup({ newIframe: crossOriginLocation });

        await expectIframeReloaded(
          'https://headless.site/$preview/foo/7/?in_preview_panel=true',
          async (newIframe) => {
            expect(window.addEventListener).not.toHaveBeenCalled();
            expect(mockScroll).not.toHaveBeenCalled();
          },
        );
      });
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
        content: [],
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
        content: [],
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
        content: [],
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
        content: [],
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
        content: [],
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
        content: [],
        ready: [expect.any(Event)],
        updated: [expect.any(Event), expect.any(Event), expect.any(Event)],
      });
    });
  });

  describe('content checks', () => {
    const mockViolations = [
      {
        id: 'landmark-complementary-is-top-level',
        impact: 'moderate',
        tags: ['cat.semantics', 'best-practice'],
        description:
          'Ensure the complementary landmark or aside is at top level',
        help: 'Aside should not be contained in another landmark',
        helpUrl:
          'https://dequeuniversity.com/rules/axe/4.10/landmark-complementary-is-top-level?application=axeAPI',
        nodes: [
          {
            any: [
              {
                id: 'landmark-is-top-level',
                data: {
                  role: null,
                },
                relatedNodes: [],
                impact: 'moderate',
                message: 'The null landmark is contained in another landmark.',
              },
            ],
            all: [],
            none: [],
            impact: 'moderate',
            html: '<aside><div><div><h4>Origin</h4><p>United States (New England)</p></div><div><h4>Type</h4><p>Yeast bread</p></div></div></aside>',
            target: ['#w-preview-iframe', 'aside'],
            failureSummary:
              'Fix any of the following:\n  The null landmark is contained in another landmark.',
          },
        ],
      },
      {
        id: 'heading-order',
        impact: 'moderate',
        tags: ['cat.semantics', 'best-practice'],
        description: 'Ensure the order of headings is semantically correct',
        help: 'Heading levels should only increase by one',
        helpUrl:
          'https://dequeuniversity.com/rules/axe/4.10/heading-order?application=axeAPI',
        nodes: [
          {
            any: [
              {
                id: 'heading-order',
                data: null,
                relatedNodes: [],
                impact: 'moderate',
                message: 'Heading order invalid',
              },
            ],
            all: [],
            none: [],
            impact: 'moderate',
            html: '<h4>Origin</h4>',
            target: ['#w-preview-iframe', 'div:nth-child(1) > h4'],
            failureSummary:
              'Fix any of the following:\n  Heading order invalid',
          },
        ],
      },
    ];

    beforeEach(() => {
      // We log accessibility violations to the console as errors,
      // mock it to avoid cluttering the test output.
      jest.spyOn(console, 'error').mockImplementation(() => {});
      document.body.insertAdjacentHTML('beforeend', checksSidePanel);

      const mockText = 'Hello world 123'.repeat(100);
      mockA11yResults = { violations: [] };
      mockExtractedContent = {
        lang: 'en',
        innerText: mockText,
        innerHTML: `<p>${mockText}</p>`,
      };
    });

    afterEach(() => {
      // eslint-disable-next-line no-console
      console.error.mockRestore();
      // Ensure disconnect() is called before the next test so that the window's
      // event listeners are removed
      document.body.innerHTML = '';
    });

    it('should run content checks on the preview and render the results', async () => {
      mockA11yResults = { violations: mockViolations };
      mockAxeResults();

      await initializeOpenedPanel();

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(1);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith(
        'axe.run results',
        mockViolations,
      );

      await Promise.resolve();

      const toggleCounter = document.querySelector(
        '[data-side-panel-toggle-counter]',
      );
      expect(toggleCounter.textContent.trim()).toEqual('2');

      const wordCount = document.querySelector('[data-content-word-count]');
      expect(wordCount.textContent.trim()).toEqual('201');

      const readingTime = document.querySelector('[data-content-reading-time]');
      expect(readingTime.textContent.trim()).toEqual('1 min');

      const readabilityScore = document.querySelector(
        '[data-content-readability-score]',
      );
      expect(readabilityScore.textContent.trim()).toEqual('Complex');

      const panelCounter = document.querySelector('[data-a11y-result-count]');
      expect(panelCounter.textContent.trim()).toEqual('2');

      const checksPanel = document.querySelector('[data-checks-panel]');
      const resultRows = checksPanel.querySelectorAll('[data-a11y-result-row]');

      // Should dispatch the content event with the extracted content and metrics
      expect(events.content).toHaveLength(1);
      expect(events.content[0].detail).toEqual({
        content: mockExtractedContent,
        metrics: {
          wordCount: 201,
          readingTime: 1,
          lixScore: expect.any(Number),
          readabilityScore: 'Complex',
        },
      });

      // Note: The sorting algorithm does not work on the preview panel because
      // the logic does not access the iframe's DOM to compare the nodes, so it
      // ends up comparing the iframe itself, thus
      expect(resultRows.length).toEqual(2);

      // Should allow custom error message and help text from the config instead
      // of Axe's defaults
      expect(
        resultRows[0]
          .querySelector('[data-a11y-result-name]')
          .textContent.trim(),
      ).toEqual('Incorrect heading hierarchy');
      expect(
        resultRows[0]
          .querySelector('[data-a11y-result-help]')
          .textContent.trim(),
      ).toEqual('Avoid skipping levels');
      // Should strip out the #w-preview-iframe selector
      expect(
        resultRows[0]
          .querySelector('[data-a11y-result-selector]')
          .textContent.trim(),
      ).toEqual('div:nth-child(1) > h4');

      // Should use Axe's error message and help text
      expect(
        resultRows[1]
          .querySelector('[data-a11y-result-name]')
          .textContent.trim(),
      ).toEqual('Aside should not be contained in another landmark');
      expect(
        resultRows[1]
          .querySelector('[data-a11y-result-help]')
          .textContent.trim(),
      ).toEqual('Ensure the complementary landmark or aside is at top level');
      // Should strip out the #w-preview-iframe selector
      const selector = resultRows[1].querySelector(
        '[data-a11y-result-selector]',
      );
      expect(selector.textContent.trim()).toEqual('aside');

      mockWindow({ open: jest.fn() });

      // Click the selector link to open the result in a new tab
      selector.click();

      // Run all timers and promises
      await jest.runAllTimersAsync();

      // Should open the result in a new tab with the correct URL
      const absoluteUrl = `http://localhost${url}`;
      expect(window.open).toHaveBeenCalledWith(absoluteUrl, absoluteUrl);
    });

    it('should not throw an error if content metrics plugin fails to return the results', async () => {
      mockA11yResults = { violations: mockViolations };
      mockExtractedContent = null;
      mockAxeResults();

      await initializeOpenedPanel();

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(1);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith(
        'axe.run results',
        mockViolations,
      );

      await Promise.resolve();

      const toggleCounter = document.querySelector(
        '[data-side-panel-toggle-counter]',
      );
      expect(toggleCounter.textContent.trim()).toEqual('2');

      const wordCount = document.querySelector('[data-content-word-count]');
      expect(wordCount.textContent.trim()).toEqual('-');

      const readingTime = document.querySelector('[data-content-reading-time]');
      expect(readingTime.textContent.trim()).toEqual('-');

      const panelCounter = document.querySelector('[data-a11y-result-count]');
      expect(panelCounter.textContent.trim()).toEqual('2');

      const checksPanel = document.querySelector('[data-checks-panel]');
      const resultRows = checksPanel.querySelectorAll('[data-a11y-result-row]');

      // Should still render accessibility results
      expect(resultRows.length).toEqual(2);
    });

    it('should re-run content checks when the window gets a message event with w-userbar:axe-ready', async () => {
      mockAxeResults();
      await initializeOpenedPanel();
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(0);

      mockA11yResults = { violations: mockViolations };
      mockAxeResults();

      // A non-Wagtail message event should not trigger the checks
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { something: { foo: 'bar' } },
        }),
      );
      await jest.runAllTimersAsync();

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(0);

      // A Wagtail message event that is unrelated should not trigger the checks
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { wagtail: { type: 'w-userbar:other' } },
        }),
      );
      await jest.runAllTimersAsync();

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(0);

      // Simulate the Wagtail userbar sending the axe-ready event to indicate
      // that it just finished running the accessibility checks and the
      // PreviewController should re-run the checks
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { wagtail: { type: 'w-userbar:axe-ready' } },
        }),
      );
      await jest.runAllTimersAsync();

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(1);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith(
        'axe.run results',
        mockViolations,
      );
      // eslint-disable-next-line no-console
      console.error.mockClear();

      // Mock two long-running checks
      mockA11yResults = new Promise((resolve) => {
        setTimeout(() => {
          resolve({ violations: [mockViolations[1]] });
        }, 5_000);
      });
      mockAxeResults();
      mockA11yResults = new Promise((resolve) => {
        setTimeout(() => {
          resolve({ violations: [mockViolations[0]] });
        }, 15_000);
      });
      mockAxeResults();

      window.dispatchEvent(
        new MessageEvent('message', {
          data: { wagtail: { type: 'w-userbar:axe-ready' } },
        }),
      );
      await jest.advanceTimersByTimeAsync(4_000);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(0);

      // If an event is dispatched while the checks are still running,
      // it will be queued and processed after the current check finishes
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { wagtail: { type: 'w-userbar:axe-ready' } },
        }),
      );
      await jest.advanceTimersByTimeAsync(5_000);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(1);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith('axe.run results', [
        mockViolations[1],
      ]);

      await jest.advanceTimersByTimeAsync(7_000);

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(2);
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith('axe.run results', [
        mockViolations[0],
      ]);
    });

    it('should allow content extraction to be executed on demand', async () => {
      mockAxeResults();
      await initializeOpenedPanel();
      const controller = application.getControllerForElementAndIdentifier(
        document.querySelector('[data-controller="w-preview"]'),
        identifier,
      );

      mockAxeResults();
      const content = await controller.extractContent();
      expect(content).toEqual(mockExtractedContent);
    });

    it('should not require opening the panel to do content extraction', async () => {
      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      const controller = application.getControllerForElementAndIdentifier(
        document.querySelector('[data-controller="w-preview"]'),
        identifier,
      );

      fetch.mockResponseSuccessJSON(validAvailableResponse);
      mockAxeResults();
      const content = controller.extractContent();
      await jest.runOnlyPendingTimersAsync();
      await expectIframeReloaded();
      expect(await content).toEqual(mockExtractedContent);
    });

    it('should auto-update while the checks panel is open', async () => {
      mockAxeResults();
      await initializeOpenedPanel();
      application.register('w-unsaved', UnsavedController);
      // Wait for the UnsavedController's delayed setup
      await jest.runOnlyPendingTimersAsync();
      const element = document.querySelector('[data-controller="w-preview"]');
      element.setAttribute('data-w-preview-auto-update-interval-value', '500');

      // Close the preview panel
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="preview"]',
      );
      sidePanelContainer.dispatchEvent(new Event('hide'));
      sidePanelContainer.hidden = true;
      await Promise.resolve();
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for the debounce
      await jest.runOnlyPendingTimersAsync();
      // No changes and the panel is closed, so no update request should be sent
      expect(global.fetch).toHaveBeenCalledTimes(0);

      // Opening the checks panel should not trigger an update request,
      // as there were no changes since the preview panel was closed
      const checksPanel = document.querySelector('[data-side-panel="checks"]');
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');
      checksPanel.dispatchEvent(new Event('show'));
      checksPanel.hidden = false;
      await Promise.resolve();
      expect(global.fetch).toHaveBeenCalledTimes(0);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      const input = document.querySelector('input[name="title"]');
      input.value = 'Changed title';

      fetch.mockResponseSuccessJSON(validAvailableResponse);
      mockAxeResults();

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce before notifying of no further changes
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce of the preview interval setting
      await jest.runOnlyPendingTimersAsync();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      // Should reload the iframe
      await expectIframeReloaded();

      // Close the checks panel
      checksPanel.dispatchEvent(new Event('hide'));
      checksPanel.hidden = true;
      await Promise.resolve();
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');

      input.value = 'Changed title again';

      // Trigger the next check interval
      await jest.runOnlyPendingTimersAsync();
      // Wait for debounce
      await jest.runOnlyPendingTimersAsync();

      // We know there are changes
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('true');
      // But the checks panel is closed, so no update request should be sent
      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseSuccessJSON(validAvailableResponse);
      mockAxeResults();

      // Opening the checks panel should now trigger an update request and
      // reload the iframe
      checksPanel.dispatchEvent(new Event('show'));
      checksPanel.hidden = false;
      await Promise.resolve();
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(element.getAttribute('data-w-preview-stale-value')).toBe('false');
      await Promise.resolve();
      await expectIframeReloaded();
    });

    it('should immediately update the preview if the panel was already open on connect', async () => {
      mockAxeResults();
      const sidePanelContainer = document.querySelector(
        '[data-side-panel="checks"]',
      );
      sidePanelContainer.dispatchEvent(new Event('show'));
      sidePanelContainer.hidden = false;
      await Promise.resolve();

      expect(global.fetch).not.toHaveBeenCalled();
      expect(events).toMatchObject({
        update: [],
        json: [],
        error: [],
        load: [],
        loaded: [],
        content: [],
        ready: [],
        updated: [],
      });

      // Should not have fetched the preview URL
      expect(global.fetch).not.toHaveBeenCalled();

      fetch.mockResponseSuccessJSON(validAvailableResponse);

      application = Application.start();
      application.register(identifier, PreviewController);
      await Promise.resolve();

      // There's no spinner, so setTimeout should not be called
      expect(setTimeout).not.toHaveBeenCalled();

      // Should send the preview data to the preview URL
      expect(global.fetch).toHaveBeenCalledWith(url, {
        body: expect.any(Object),
        method: 'POST',
      });

      // At this point, there should only be one fetch call (upon connect)
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Initially, the iframe src should be empty so it doesn't load the preview
      // until after the request is complete
      const iframes = document.querySelectorAll('iframe');
      expect(iframes.length).toEqual(1);
      expect(iframes[0].src).toEqual('');

      // Simulate the request completing
      await Promise.resolve();
      await Promise.resolve();

      await expectIframeReloaded();

      // If content checks are enabled, there are a few more promises to resolve
      await jest.runOnlyPendingTimersAsync();

      expect(events).toMatchObject({
        update: [expect.any(Event)],
        json: [expect.any(Event)],
        error: [],
        load: [expect.any(Event)],
        loaded: [expect.any(Event)],
        content: [expect.any(Event)],
        ready: [expect.any(Event)],
        updated: [expect.any(Event)],
      });
    });

    it('should clean up event listeners on disconnect', async () => {
      mockAxeResults();
      const panel = document.querySelector('[data-side-panel="checks"]');
      const element = document.querySelector('[data-controller="w-preview"]');
      const spies = [
        jest.spyOn(panel, 'addEventListener'),
        jest.spyOn(panel, 'removeEventListener'),
        jest.spyOn(window, 'addEventListener'),
        jest.spyOn(window, 'removeEventListener'),
      ];

      await initializeOpenedPanel();

      const controller = application.getControllerForElementAndIdentifier(
        element,
        identifier,
      );

      expect(window.addEventListener).toHaveBeenCalledWith(
        'message',
        controller.runChecks,
      );
      expect(panel.addEventListener).toHaveBeenCalledWith(
        'show',
        controller.checkAndUpdatePreview,
      );

      element.removeAttribute('data-controller');
      await jest.runAllTimersAsync();

      expect(window.removeEventListener).toHaveBeenCalledWith(
        'message',
        controller.runChecks,
      );
      expect(panel.removeEventListener).toHaveBeenCalledWith(
        'show',
        controller.checkAndUpdatePreview,
      );

      spies.forEach((spy) => spy.mockRestore());
      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledTimes(0);
    });

    describe('custom axe configuration', () => {
      it('should convert axe context config for the preview iframe', async () => {
        mockAxeResults();
        await initializeOpenedPanel();
        expect(axe.run).toHaveBeenCalledWith(
          {
            include: {
              fromFrames: ['#w-preview-iframe', 'main'],
            },
          },
          axeConfig.options,
        );
      });

      it('should respect context.exclude', async () => {
        const config = document.getElementById(
          'accessibility-axe-configuration',
        );
        config.innerHTML = JSON.stringify({
          ...axeConfig,
          context: {
            include: ['#main'],
            exclude: ['[data-ignored]'],
          },
        });

        mockAxeResults();
        await initializeOpenedPanel();
        expect(axe.run).toHaveBeenCalledWith(
          {
            include: {
              fromFrames: ['#w-preview-iframe', '#main'],
            },
            exclude: {
              fromFrames: ['#w-preview-iframe', '[data-ignored]'],
            },
          },
          axeConfig.options,
        );
      });
    });
  });
});
