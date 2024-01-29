import { Application } from '@hotwired/stimulus';
import { TabsController } from './TabsController';

jest.useFakeTimers()

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

  describe("checks ARIA attributes", () => {
    beforeEach(async () => {
      await setup(`
       <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-active-value="" data-w-tabs-animate-class="animate-in" data-w-tabs-animate-value="false">
         <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
             <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab"
                tabindex="-1" data-action="click->w-tabs#handleTabChange:prevent keydown->w-tabs#handleKeydown" data-w-tabs-target="label">
               Tab 1
             </a>
             <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
                data-action="click->w-tabs#handleTabChange:prevent keydown->w-tabs#handleKeydown" data-w-tabs-target="label">
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
      `)
    })

    it("should have aria-selected set to the first tab on connect", () => {
      const label = document.getElementById("tab-label-tab-1");

      expect(label.getAttribute("aria-selected")).toBe("true");
      expect(label.tabIndex).toBe(0); // Ensure first tab is focusable
    });

    it("should set aria-selected to the appropriate tab when a tab is clicked", async () => {
      const tab2Label = document.getElementById("tab-label-tab-2");
      const tab1Panel = document.getElementById("tab-tab-1");

      tab2Label.dispatchEvent(new MouseEvent("click"))
      await jest.runAllTimersAsync();

      expect(document.getElementById("tab-label-tab-1").getAttribute("aria-selected")).toBe("false");
      expect(tab2Label.getAttribute("aria-selected")).toBe("true");
      expect(tab1Panel.hidden).toBeTruthy();
    });
  })
})