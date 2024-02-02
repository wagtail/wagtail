import { Application } from '@hotwired/stimulus';
import { TabsController } from './TabsController';

function simulateKeydown(key) {
  const event = new KeyboardEvent('keydown', {
    key,
    code: key,
    bubbles: true,
    cancelable: true,
  });
  document.activeElement.dispatchEvent(event);
}

jest.useFakeTimers();

describe('TabsController', () => {
  let app;
  const oldWindowLocation = window.location;

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    app = Application.start();
    app.register('w-tabs', TabsController);
    await Promise.resolve();
  };

  beforeAll(() => {
    delete window.location;

    window.location = Object.defineProperties(
      {},
      {
        ...Object.getOwnPropertyDescriptors(oldWindowLocation),
        assign: { configurable: true, value: jest.fn() },
      },
    );
  });

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('checks ARIA attributes', () => {
    beforeEach(async () => {
      await setup(`
        <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-selected-value="" data-w-tabs-selected-class="animate-in">
            <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
                <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab" tabindex="-1"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 1
                </a>
                <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 2
                </a>
            </div>
            <div class="tab-content tab-content--comments-enabled">
                <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
                    tab-1
                </section>
                <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
                    tab-2
                </section>
            </div>
        </div>
      `);
    });

    it('should have aria-selected set to the first tab on connect', () => {
      const label = document.getElementById('tab-label-tab-1');

      expect(label.getAttribute('aria-selected')).toBe('true');
      expect(label.tabIndex).toBe(0); // Ensure first tab is focusable
    });

    it('should set aria-selected to the appropriate tab when a tab is clicked', async () => {
      const tab2Label = document.getElementById('tab-label-tab-2');
      const tab2Panel = document.getElementById('tab-tab-2');
      const tab1Label = document.getElementById('tab-label-tab-1');
      const tab1Panel = document.getElementById('tab-tab-1');

      tab2Label.dispatchEvent(new MouseEvent('click'));
      await jest.runAllTimersAsync();

      expect(tab1Label.getAttribute('aria-selected')).toBe('false');
      expect(tab2Label.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
    });
  });

  it('should set correct classes according', async () => {
    const tab2Label = document.getElementById('tab-label-tab-2');
    const tab2Panel = document.getElementById('tab-tab-2');
    const tab1Label = document.getElementById('tab-label-tab-1');
    const tab1Panel = document.getElementById('tab-tab-1');
    const selectedClass = document
      .querySelector('[class="w-tabs"]')
      .getAttribute('data-w-tabs-selected-class');

    tab2Label.dispatchEvent(new MouseEvent('click'));
    await jest.runAllTimersAsync();

    expect(tab1Label.getAttribute('aria-selected')).toBe('false');
    expect(tab2Label.getAttribute('aria-selected')).toBe('true');
    expect(tab2Panel.className).toContain(selectedClass);
    expect(tab1Panel.hidden).toBeTruthy();
  });

  describe('browser based', () => {
    it('should have tab select when active value is given', async () => {
      await setup(`
        <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-selected-value="tab-tab-2" data-w-tabs-selected-class="animate-in">
            <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
                <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab" tabindex="-1"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 1
                </a>
                <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 2
                </a>
            </div>
            <div class="tab-content tab-content--comments-enabled">
                <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
                    tab-1
                </section>
                <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
                    tab-2
                </section>
            </div>
        </div>
      `);
      const tab2Label = document.querySelector('#tab-label-tab-2');
      const tab2Panel = document.querySelector('#tab-tab-2');
      const tab1Panel = document.querySelector('#tab-tab-1');

      await jest.runAllTimersAsync();
      expect(window.location.hash).toBe('#tab-tab-2');
      expect(tab2Label.getAttribute('aria-selected')).toBe('true');
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab1Panel.hidden).toBeTruthy();
    });

    it('should have active tab to second tab', async () => {
      window.location.hash = '#tab-tab-2';

      await setup(`
        <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-selected-value="" data-w-tabs-selected-class="animate-in">
            <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
                <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab" tabindex="-1"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 1
                </a>
                <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
                  data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                    Tab 2
                </a>
            </div>
            <div class="tab-content tab-content--comments-enabled">
                <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
                    tab-1
                </section>
                <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
                    tab-2
                </section>
            </div>
        </div>
      `);

      await jest.runAllTimersAsync();
      const tab2Label = document.querySelector('#tab-label-tab-2');
      const tab2Panel = document.querySelector('#tab-tab-2');
      const tab1Panel = document.querySelector('#tab-tab-1');

      expect(window.location.hash).toBe('#tab-tab-2');
      expect(tab2Label.getAttribute('aria-selected')).toBe('true');
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab1Panel.hidden).toBeTruthy();
    });
  });

  describe('checks keyboard navigations', () => {
    beforeEach(async () => {
      await setup(`
        <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-selected-value="" data-w-tabs-selected-class="animate-in">
          <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
              <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab" tabindex="-1"
                data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                  Tab 1
              </a>
              <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
                data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
                  Tab 2
              </a>
          </div>
          <div class="tab-content tab-content--comments-enabled">
              <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
                  tab-1
              </section>
              <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
                  tab-2
              </section>
          </div>
        </div>
      `);
    });
    describe('arrow keys', () => {
      it('should switch to right tab on right arrow key presss', async () => {
        const tab1Label = document.getElementById('tab-label-tab-1');
        const tab2Label = document.getElementById('tab-label-tab-2');

        tab1Label.focus();
        simulateKeydown('ArrowRight');
        await jest.runAllTimersAsync();

        expect(tab2Label.getAttribute('aria-selected')).toBe('true');
      });
      it('should switch to left tab on left arrow key presss', async () => {
        const tab1Label = document.getElementById('tab-label-tab-1');
        const tab2Label = document.getElementById('tab-label-tab-2');

        tab2Label.focus();
        simulateKeydown('ArrowLeft');
        await jest.runAllTimersAsync();

        expect(tab1Label.getAttribute('aria-selected')).toBe('true');
      });
    });

    describe('home and end keys', () => {
      it('should focus first tab on home key press', async () => {
        const tab1Label = document.getElementById('tab-label-tab-1');
        const tab2Label = document.getElementById('tab-label-tab-2');

        tab2Label.focus();
        simulateKeydown('Home');
        await jest.runAllTimersAsync();

        expect(tab1Label).toBe(document.activeElement);
      });

      it('should focus first tab on end key press', async () => {
        const tab1Label = document.getElementById('tab-label-tab-1');
        const tab2Label = document.getElementById('tab-label-tab-2');

        tab1Label.focus();
        simulateKeydown('End');
        await jest.runAllTimersAsync();

        expect(tab2Label).toBe(document.activeElement);
      });
    });
  });
});
