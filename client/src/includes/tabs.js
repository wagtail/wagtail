const DEFAULT_OPTIONS = {
  tabActiveClass: 'active',
  paneActiveClass: 'active',
  tabLinkSelector: '[role="tab"]',
  initialActiveTab: 0,
};

class TabInterface {
  /**
   * TabInterface expects to be provided an element which is the ancestor of all
   * tabs the interface includes, most likely an element with role="tablist"
   *
   * Tab elements should either be the tab list's immediate children or listed
   * in the tab list's aria-owns property.
   *
   * To specify which tab is active first, ensure that tab has the active class.
   * Otherwise TabInterface will automatically activate the first tab.
   *
   * TabInterface will handle filling in aria-selected, aria-controls,
   * aria-labelledby, and hidden html attributes. Please ensure that the HTML
   * contains appropriate role attributes and that each tab has either an href
   * _or_ an aria-control attribute pointing to the appropriate tab panel.
   */
  constructor(el, options) {
    // If this element has already been instantiated as a tabpanel, bail early
    if ('wagtailTabInterface' in el) return;

    this.el = el;
    this.el.wagtailTabInterface = this;

    this.options = Object.assign({}, DEFAULT_OPTIONS, options);

    this.handleKeypress = this.handleKeypress.bind(this);
    this.setActiveTab = this.setActiveTab.bind(this);
    this.render = this.render.bind(this);

    this.tabs = [...this.el.querySelectorAll(this.options.tabLinkSelector)];

    this.activeTab = this.tabs[this.options.initialActiveTab];

    this.setUpTabs();

    // If there's a tab that already has the active class, activate it instead
    const activeClassTab = this.el.querySelector(`${this.options.tabLinkSelector}.${this.options.tabActiveClass}`);
    if (activeClassTab) {
      this.activeTab = activeClassTab;
    }

    // If there's a tab that matches the location hash, activate it instead
    if (window.location.hash) {
      const activeHashTab = this.el.querySelector(`[href="${window.location.hash}"]`);
      if (activeHashTab) {
        this.activeTab = activeHashTab;
      }
    }

    // Run render to ensure attributes are all properly set
    this.render();
  }

  /** Add initial properties and listeners to tabs */
  setUpTabs() {
    const tabs = this.tabs;
    tabs.forEach(tab => {
      let tabPanelId;

      // Add click and arrow key behavior to tab
      tab.addEventListener('click', this.setActiveTab);
      tab.addEventListener('keydown', this.handleKeypress);

      // Add aria attributes to the tab
      if (tab.href) {
        tabPanelId = tab.href.split('#')[1];
        tab.setAttribute('aria-controls', tabPanelId);
      } else {
        tabPanelId = tab.getAttribute('aria-controls');
      }

      // Assuming a matching tabPanel exists, set the appropriate attributes
      // on that panel
      const tabId = tab.id;
      const tabPanel = document.getElementById(tabPanelId);
      if (tabPanel) {
        tabPanel.setAttribute('aria-labelledby', tabId);
      }
    });
  }

  handleKeypress(evt) {
    const currentTabIndex = this.tabs.indexOf(this.activeTab);
    const nextTabIndex = (currentTabIndex + 1) % this.tabs.length;
    const prevTabIndex = (currentTabIndex - 1 + this.tabs.length) % this.tabs.length;
    // Click and focus on the appropriate next or previous tab
    if (evt.keyCode === 37) { // ←
      this.tabs[prevTabIndex].click();
      this.tabs[prevTabIndex].focus();
    } else if (evt.keyCode === 39) { // →
      this.tabs[nextTabIndex].click();
      this.tabs[nextTabIndex].focus();
    }
  }

  /**
   * setActiveTab changes the currently active tab in an interface. It accepts
   * three argument types:
   * - an integer index
   * - the tab DOM element
   * - an Event triggered by the tab DOM element
   */
  setActiveTab(arg) {
    let targetTab;

    // Handle these cases: arg is event-like, arg is integer index, arg is element
    if (arg instanceof Event) {
      // Extract DOM element from event
      targetTab = arg.target;
    } else if (typeof arg === 'number') {
      // Use arg as in index
      targetTab = self.tabs[arg];
    } else {
      // Assume it's a DOM element
      targetTab = arg;
    }

    // If the clicked tab is already active, bail out
    if (this.activeTab === targetTab) return;

    this.activeTab = targetTab;
    window.history.replaceState(null, null, this.activeTab.href);
    this.render();

    // If arg is an event, stop propagation and prevent default behavior
    if (arg instanceof Event) {
      arg.stopPropagation();
      arg.preventDefault();
    }
  }

  /**
   * Update all tabs and tabpanels to be selected or not in DOM attributes,
   * reading from the value of this.activeTab
   */
  render() {
    this.tabs.forEach(tab => {
      let pane;
      if (tab === this.activeTab) {
        // Add active class and ARIA attribute to active tab
        tab.classList.add(this.options.tabActiveClass);
        tab.setAttribute('aria-selected', 'true');
        // Show active pane
        pane = document.getElementById(tab.getAttribute('aria-controls'));
        if (pane) {
          pane.setAttribute('tabindex', '0');
          pane.classList.add(this.options.paneActiveClass);
          pane.hidden = false;
        }
      } else {
        // Remove active class and ARIA attribute from any inactive tab
        tab.classList.remove(this.options.tabActiveClass);
        tab.setAttribute('aria-selected', 'false');
        // Hide inactive panes
        pane = document.getElementById(tab.getAttribute('aria-controls'));
        if (pane) {
          pane.setAttribute('tabindex', '-1');
          pane.classList.remove(this.options.paneActiveClass);
          pane.hidden = true;
        }
      }
    });
  }
}

const initDefaultTabs = () => {
  const tabPanels = [...document.querySelectorAll('.tab-nav')];
  tabPanels.forEach(el => new TabInterface(el));
  // Tab toggles have special behavior where they trigger a tab to be clicked
  // at a distance. They must have a href that matches the tab to be activated
  const tabToggles = [...document.querySelectorAll('.tab-toggle')];
  tabToggles.forEach(el => {
    el.addEventListener('click', evt => {
      // Find the first tab element with a matching href and click on it
      const href = '#' + evt.currentTarget.href.split('#')[1];
      document.querySelector(`[href$="${href}"][role="tab"]`).click();
      evt.stopPropagation();
    });
  });
};

export { TabInterface, initDefaultTabs };
