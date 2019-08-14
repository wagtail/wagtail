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

describe('TabInterface', () => {
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
    tabInterface = null;
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
  });
});
