import { Application } from '@hotwired/stimulus';
import { PreviewController } from './PreviewController';

describe('PreviewController', () => {
  let application;
  const resizeObserverMockObserve = jest.fn();
  const resizeObserverMockUnobserve = jest.fn();
  const resizeObserverMockDisconnect = jest.fn();

  const ResizeObserverMock = jest.fn().mockImplementation(() => ({
    observe: resizeObserverMockObserve,
    unobserve: resizeObserverMockUnobserve,
    disconnect: resizeObserverMockDisconnect,
  }));

  global.ResizeObserver = ResizeObserverMock;

  const url = '/preview/';
  const spinner = /* html */ `
    <div data-w-preview-target="spinner" hidden>
      <svg class="icon icon-spinner default" aria-hidden="true">
        <use href="#icon-spinner"></use>
      </svg>
      <span class="w-sr-only">Loading</span>
    </div>
  `;

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
    document.body.innerHTML = /* html */ `
      <div data-side-panel="preview">
        <h2 id="side-panel-preview-title">Preview</h2>
        <div
          class="w-preview"
          data-controller="w-preview"
          data-w-preview-unavailable-class="w-preview--unavailable"
          data-w-preview-has-errors-class="w-preview--has-errors"
          data-w-preview-selected-size-class="w-preview__size-button--selected"
          data-w-preview-url-value="/admin/pages/1/edit/preview/"
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
  });

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
    localStorage.removeItem('wagtail:preview-panel-device');
  });

  it('should set the device size accordingly when the input changes', async () => {
    localStorage.removeItem('wagtail:preview-panel-device');
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
    localStorage.removeItem('wagtail:preview-panel-device');
  });
});
