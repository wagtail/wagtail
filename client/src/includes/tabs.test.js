import { validateCreationForm } from './chooserModal';
import { initTabs } from './tabs';

describe('tabs', () => {
  beforeEach(() => {
    document.body.innerHTML = /* html */ `
      <div data-tabs>
        <div role="tablist">
          <a
            id="tab-label-content"
            href="#tab-content"
            role="tab"
            aria-selected="false"
            tabindex="-1"
            aria-controls="tab-content"
          >
            Content
          </a>

          <a
            id="tab-label-promote"
            href="#tab-promote"
            role="tab"
            aria-selected="false"
            aria-controls="tab-promote"
          >
            Promote
          </a>
        </div>

        <div>
          <section
            id="tab-content"
            role="tabpanel"
            aria-labelledby="tab-label-content"
            hidden
          >
            <section id="panel-child-content-title-section" data-panel>
              <div id="panel-child-content-title-content">
                <div data-field data-contentpath="title">
                  <input
                    type="text"
                    name="title"
                    maxlength="255"
                    required
                    id="id_title"
                  />
                </div>
              </div>
            </section>
          </section>

          <section
            id="tab-promote"
            role="tabpanel"
            aria-labelledby="tab-label-promote"
            hidden
          >
            <section
              id="panel-child-promote-for_search_engines-section"
              data-panel
            >
              <label
                for="id_search_description"
                id="id_search_description-label"
              >
                Meta description
              </label>

              <div data-field data-contentpath="search_description">
                <textarea
                  name="search_description"
                  id="id_search_description"
                ></textarea>
              </div>
            </section>
          </section>
        </div>
      </div>
    `;
  });

  describe('initialize selected tab', () => {
    afterEach(() => {
      window.location.hash = '';
    });

    it('should select the first tab by default', async () => {
      initTabs();
      await Promise.resolve();

      const contentTab = document.getElementById('tab-content');
      const promoteTab = document.getElementById('tab-promote');
      const contentTabLabel = document.getElementById('tab-label-content');
      const promoteTabLabel = document.getElementById('tab-label-promote');

      expect(contentTab.hasAttribute('hidden')).toBe(false);
      expect(promoteTab.hasAttribute('hidden')).toBe(true);

      expect(contentTabLabel.getAttribute('aria-selected')).toEqual('true');
      expect(promoteTabLabel.getAttribute('aria-selected')).toEqual('false');
    });

    it('should select the correct tab where the anchored element lives', async () => {
      window.location.hash = '#id_search_description';
      initTabs();
      await Promise.resolve();

      const contentTab = document.getElementById('tab-content');
      const promoteTab = document.getElementById('tab-promote');
      const contentTabLabel = document.getElementById('tab-label-content');
      const promoteTabLabel = document.getElementById('tab-label-promote');

      expect(contentTab.hasAttribute('hidden')).toBe(true);
      expect(promoteTab.hasAttribute('hidden')).toBe(false);

      expect(contentTabLabel.getAttribute('aria-selected')).toEqual('false');
      expect(promoteTabLabel.getAttribute('aria-selected')).toEqual('true');
    });

    it('should select the correct tab where the element pointed by the contentpath directive lives', async () => {
      window.location.hash = '#:w:contentpath=search_description';
      initTabs();
      await Promise.resolve();

      const contentTab = document.getElementById('tab-content');
      const promoteTab = document.getElementById('tab-promote');
      const contentTabLabel = document.getElementById('tab-label-content');
      const promoteTabLabel = document.getElementById('tab-label-promote');

      expect(contentTab.hasAttribute('hidden')).toBe(true);
      expect(promoteTab.hasAttribute('hidden')).toBe(false);

      expect(contentTabLabel.getAttribute('aria-selected')).toEqual('false');
      expect(promoteTabLabel.getAttribute('aria-selected')).toEqual('true');
    });

    it('should not throw an error if the URL hash begins with a number', async () => {
      window.location.hash = '#123abcd';
      initTabs();
      await Promise.resolve();

      const contentTab = document.getElementById('tab-content');
      const promoteTab = document.getElementById('tab-promote');
      const contentTabLabel = document.getElementById('tab-label-content');
      const promoteTabLabel = document.getElementById('tab-label-promote');

      expect(contentTab.hasAttribute('hidden')).toBe(false);
      expect(promoteTab.hasAttribute('hidden')).toBe(true);

      expect(contentTabLabel.getAttribute('aria-selected')).toEqual('true');
      expect(promoteTabLabel.getAttribute('aria-selected')).toEqual('false');
    });
  });

  describe('switching tabs', () => {
    it('should allow switching to a different tab by clicking on the label', async () => {
      initTabs();
      await Promise.resolve();

      const contentTab = document.getElementById('tab-content');
      const promoteTab = document.getElementById('tab-promote');
      const contentTabLabel = document.getElementById('tab-label-content');
      const promoteTabLabel = document.getElementById('tab-label-promote');

      promoteTabLabel.click();

      expect(contentTab.hasAttribute('hidden')).toBe(true);
      expect(promoteTab.hasAttribute('hidden')).toBe(false);

      expect(contentTabLabel.getAttribute('aria-selected')).toEqual('false');
      expect(promoteTabLabel.getAttribute('aria-selected')).toEqual('true');
    });
  });
});
