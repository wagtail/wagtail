const DEFAULT_OPTIONS = {
  tabActiveClass: 'active',
  paneActiveClass: 'active',
  tabLinkSelector: 'li > a',
  initialActiveTab: 0,
};

class TabInterface {
  /**
   * TabInterface expects to be provided an element which is the ancestor of all
   * tabs the interface includes, most likely an element with role="tablist"
   */
  constructor(el, options) {
    // If this element has already been instantiated as a tabpanel, bail early
    if ('wagtailTabInterface' in el) return;

    this.el = el;
    this.el.wagtailTabInterface = this;

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
        this.setActiveTab(newActiveTab);
        return; // Early return to avoid a rerender
      }
    }

    // Run render to ensure attributes are all properly set
    this.render();
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
          pane.classList.remove(this.options.paneActiveClass);
          pane.hidden = true;
        }
      }
    });
  }
}

const initDefaultTabs = () => {
  const tabPanels = Array.from(document.querySelectorAll('.tab-nav'));
  tabPanels.forEach(el => new TabInterface(el));
};

export { TabInterface, initDefaultTabs };
