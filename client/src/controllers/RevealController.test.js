import { Application } from '@hotwired/stimulus';
import RevealController from './RevealController';

describe('RevealController', () => {
  let application;
  beforeEach(() => {
    application?.stop();
    document.body.innerHTML = `
  <section class="w-panel" w-panel >
        <div class="w-panel__header" data-controller="w-panel">
            <a class="w-panel__anchor w-panel__anchor--prefix" w-panel-anchor >
            </a>
            <button class="w-panel__toggle" type="button"  data-action="click->w-panel#toggle" aria-expanded="true">
            </button>
                <h2 class="w-panel__heading w-panel__heading--label" w-panel-heading>
                        <label><span w-panel-heading-text></span><span class="w-required-mark" w-panel-required></span></label>
                        <span w-panel-heading-text></span><span class="w-required-mark" w-panel-required></span>
                </h2>
            <a class="w-panel__anchor w-panel__anchor--suffix" >
            </a>
            <div class="w-panel__divider"></div>
                <div class="w-panel__controls" w-panel-controls>
                    <div class="w-panel__controls-cue">
                    </div>
                </div>
        </div>

    <div class="w-panel__content hidden" data-w-panel-target="item">
    </div>
</section>
  `;
    application = Application.start();
    application.register('reveal', RevealController);
  });
  describe('#toggle', () => {
    it('should reveal the target', () => {
      var button = document.querySelector('[data-w-panel-toggle]');
      var hidden = document.querySelector('[data-w-panel-target]');
      expect(hidden.className).toContain('hidden');
      button.click();
      expect(hidden.className).not.toContain('hidden');
      button.click();
      expect(hidden.className).toContain('hidden');
    });
  });
});
