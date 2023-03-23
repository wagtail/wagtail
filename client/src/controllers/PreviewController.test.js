import { Application } from '@hotwired/stimulus';
import { PreviewController } from './PreviewController';

describe('PreviewController', () => {
  let application;
  const url = '/preview/';

  beforeEach(() => {
    document.body.innerHTML = `
    <div
      class="preview-panel preview-panel--mobile"
      data-controller="w-preview"
      data-action="${url}"
    >
    </div>
    `;
  });

  afterEach(() => {
    application.stop();
  });

  it('should start the application', async () => {
    // start application
    application = Application.start();
    application.register('w-preview', PreviewController);
  });
});
