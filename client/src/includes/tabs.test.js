import {
  TabInterface,
  initDefaultTabs,
} from './tabs';

const BASIC_TAB_HTML = `
  <div id="tabs" role="tablist">
    <a href="#t1" role="tab" id="t1-label">Tab 1</a>
    <a href="#t2" role="tab" id="t2-label">Tab 2</a>
  </div>
  <div id="tabPanels">
    <div id="t1" role="tabpanel">
    </div>
    <div id="t2" role="tabpanel">
    </div>
  </div>
`;

const SECOND_TAB_SELECTED_HTML = `
  <div id="tabs" role="tablist">
    <a href="#t1" role="tab" id="t1-label">Tab 1</a>
    <a href="#t2" class="active" role="tab" id="t2-label">Tab 2</a>
  </div>
  <div id="tabPanels">
    <div id="t1" role="tabpanel">
    </div>
    <div id="t2" role="tabpanel">
    </div>
  </div>
`;

const DEFAULT_TAB_HTML = `
  <div class="tab-nav" id="tabs" role="tablist">
    <a href="#t1" role="tab" id="t1-label">Tab 1</a>
    <a href="#t2" class="active" role="tab" id="t2-label">Tab 2</a>
  </div>
  <div id="tabPanels">
    <div id="t1" role="tabpanel">
    </div>
    <div id="t2" role="tabpanel">
    </div>
  </div>
`;

describe('TabInterface', () => {
  describe('using basic HTML and configuration', () => {
    let tabList;
    let tab1;
    let tab2;
    let panel1;
    let panel2;
    let tabInterface;

    beforeEach(() => {
      document.body.innerHTML = BASIC_TAB_HTML;
      tabList = document.getElementById('tabs');
      tab1 = document.getElementById('t1-label');
      tab2 = document.getElementById('t2-label');
      panel1 = document.getElementById('t1');
      panel2 = document.getElementById('t2');
      tabInterface = new TabInterface(tabList);
    });

    afterEach(() => {
      document.getElementsByTagName('html')[0].innerHTML = '';
      window.location.hash = '';
    });

    it('exists', () => expect(TabInterface).toBeDefined());

    it('instantiates', () => {
      expect(tabList.wagtailTabInterface).toBeInstanceOf(TabInterface);
    });

    it('adds accessibility properties', () => {
      expect(tab1.getAttribute('aria-controls')).toEqual('t1');
      expect(tab2.getAttribute('aria-controls')).toEqual('t2');
      expect(tab1.getAttribute('aria-selected')).toEqual('true');
      expect(tab2.getAttribute('aria-selected')).toEqual('false');
      expect(panel1.getAttribute('aria-labelledby')).toEqual('t1-label');
      expect(panel2.getAttribute('aria-labelledby')).toEqual('t2-label');
      expect(panel1.hasAttribute('hidden')).toEqual(false);
      expect(panel2.hasAttribute('hidden')).toEqual(true);
    });

    it('defaults to first tab active', () => {
      // Ensure tabInterface reports correctly active tab
      expect(tabInterface.activeTab).toEqual(tab1);
      // Ensure properties are set correctly on the tabs
      expect(tab1.classList.contains('active')).toEqual(true);
      expect(tab1.getAttribute('aria-selected')).toEqual('true');
      expect(tab2.classList.contains('active')).toEqual(false);
      expect(tab2.getAttribute('aria-selected')).toEqual('false');
      // Ensure properties are set correctly on the panels
      expect(panel1.classList.contains('active')).toEqual(true);
      expect(panel1.hasAttribute('hidden')).toEqual(false);
      expect(panel2.classList.contains('active')).toEqual(false);
      expect(panel2.hasAttribute('hidden')).toEqual(true);
    });

    it('lets you change tabs on click', () => {
      tab2.click();
      // Ensure tabInterface reports correctly active tab
      expect(tabInterface.activeTab).toEqual(tab2);
      // Ensure properties are changed correctly on the tabs
      expect(tab1.classList.contains('active')).toEqual(false);
      expect(tab1.getAttribute('aria-selected')).toEqual('false');
      expect(tab2.classList.contains('active')).toEqual(true);
      expect(tab2.getAttribute('aria-selected')).toEqual('true');
      // Ensure properties are changed correctly on the panels
      expect(panel1.classList.contains('active')).toEqual(false);
      expect(panel1.hasAttribute('hidden')).toEqual(true);
      expect(panel2.classList.contains('active')).toEqual(true);
      expect(panel2.hasAttribute('hidden')).toEqual(false);
    });

    it('changes to next tab on right arrow press', () => {
      const evt = new KeyboardEvent('keydown', { keyCode: 39 });
      tab1.dispatchEvent(evt);
      // Ensure tabInterface reports correctly active tab
      expect(tabInterface.activeTab).toEqual(tab2);
      tab2.dispatchEvent(evt);
      // Ensure it wraps around back to tab 1
      expect(tabInterface.activeTab).toEqual(tab1);
    });

    it('changes to previous tab on left arrow press', () => {
      const evt = new KeyboardEvent('keydown', { keyCode: 37 });
      tab1.dispatchEvent(evt);
      // Ensure it wraps around back to tab 2
      expect(tabInterface.activeTab).toEqual(tab2);
      tab2.dispatchEvent(evt);
      // Ensure it steps back to tab 1
      expect(tabInterface.activeTab).toEqual(tab1);
    });

    it('changes the location hash to match the active tab', () => {
      tab2.click();
      expect(window.location.hash).toEqual('#t2');
      tab1.click();
      expect(window.location.hash).toEqual('#t1');
    });
  });

  describe('using different HTML or configuration', () => {
    afterEach(() => {
      document.body.innerHTML = '';
      window.location.hash = '';
    });

    it('auto-activates tab with the "active" class', () => {
      // Setup
      document.body.innerHTML = SECOND_TAB_SELECTED_HTML;
      const tabList = document.getElementById('tabs');
      const tab2 = document.getElementById('t2-label');
      const tabInterface = new TabInterface(tabList);
      // tab 2 should be immediately active
      expect(tabInterface.activeTab).toEqual(tab2);
    });

    it('auto-activates tab specified by the location hash', () => {
      // Setup
      window.location.hash = '#t2';
      document.body.innerHTML = BASIC_TAB_HTML;
      const tabList = document.getElementById('tabs');
      const tab2 = document.getElementById('t2-label');
      const tabInterface = new TabInterface(tabList);
      // tab 2 should be immediately active
      expect(tabInterface.activeTab).toEqual(tab2);
    });
  });

  describe('using initDefaultTabs', () => {
    it('initializes a tab interface on any element with class "tab-nav"', () => {
      document.body.innerHTML = DEFAULT_TAB_HTML;
      initDefaultTabs();
      const tabList = document.getElementById('tabs');
      // Verify that a TabInterface was instantiated around the tabs
      expect(tabList.wagtailTabInterface).toBeInstanceOf(TabInterface);
    });
  });
});
