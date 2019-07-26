const DEFAULT_OPTIONS = {
  tabActiveClass: 'active',
  paneActiveClass: 'active',
  tabLinkSelector: 'li > a',
  initialActiveTab: 0,
};

class TabPanel {
  constructor(el, options) {
    // If this element has already been instantiated as a tabpanel, bail early
    if ('WTTabpanel' in el) return;

    this.el = el;
    this.el.WTTabpanel = this;

    this.options = Object.assign({}, DEFAULT_OPTIONS, options);

    this.setActiveTab = this.setActiveTab.bind(this);
    this.render = this.render.bind(this);

    this.tabs = Array.from(this.el.querySelectorAll(this.options.tabLinkSelector));
    this.activeTab = this.tabs[this.options.initialActiveTab];

    this.tabs.forEach(tab => tab.addEventListener('click', this.setActiveTab));

    if (window.location.hash) {
      // If there's a tab that matches the location hash, activate it
      const newActiveTab = this.el.querySelector(`[href="${window.location.hash}"]`);
      if (newActiveTab) {
        // Simulate a click to activate tab. Triggers a render
        newActiveTab.click();
        return; // Early return to avoid a rerender
      }
    }

    // Run render to ensure attributes are all properly set
    this.render();
  }

  setActiveTab(evt) {
    // If the clicked tab is already active, bail out
    if (this.activeTab === evt.target) return;

    this.activeTab = evt.target;
    window.history.replaceState(null, null, this.activeTab.href);
    this.render();
    evt.stopPropagation();
    evt.preventDefault();
  }

  render() {
    this.tabs.forEach(tab => {
      let pane;
      if (tab === this.activeTab) {
        // Add active class and ARIA attribute to active tab
        tab.classList.add(this.options.tabActiveClass);
        tab.setAttribute('aria-selected', 'true');
        // Show active pane
        pane = document.getElementById(tab.getAttribute('aria-controls'));
        pane.classList.add(this.options.paneActiveClass);
        pane.hidden = false;
      } else {
        // Remove active class and ARIA attribute from any inactive tab
        tab.classList.remove(this.options.tabActiveClass);
        tab.setAttribute('aria-selected', 'false');
        // Hide inactive panes
        pane = document.getElementById(tab.getAttribute('aria-controls'));
        pane.classList.remove(this.options.paneActiveClass);
        pane.hidden = true;
      }
    });
  }
}

const initDefaultTabs = () => {
  const tabPanels = Array.from(document.querySelectorAll('.tab-nav'));
  tabPanels.forEach(el => new TabPanel(el));
};

export { TabPanel, initDefaultTabs };
