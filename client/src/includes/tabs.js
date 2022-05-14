/**
 *  All tabs and tab content must be nested in an element with the data-tab attribute
 *  All tab buttons need the role="tab" attr and an href with the tab content ID
 *  Tab contents need to have the role="tabpanel" attribute and and ID attribute that matches the href of the tab link.
 *  Tab buttons should also be wrapped in an element with the role="tablist" attribute
 *  Use the attribute data-tab-trigger on an Anchor link and set the href to the #ID of the tab you would like to trigger
 */
class Tabs {
  constructor(node) {
    this.tabContainer = node;
    this.tabButtons = this.tabContainer.querySelectorAll('[role="tab"]');
    this.tabList = this.tabContainer.querySelector('[role="tablist"]');
    this.tabPanels = this.tabContainer.querySelectorAll('[role="tabpanel"]');
    // External anchors that can be used for selecting tabs
    this.tabTriggerLinks =
      this.tabContainer.querySelectorAll('[data-tab-trigger]');
    this.keydownEventListener = this.keydownEventListener.bind(this);

    // Tab Options - Add these data attributes along side the data-tabs attribute
    // Use this to enable fade-in animations on tab select
    this.animate = this.tabContainer.hasAttribute('data-tabs-animate');
    // Disable url hash from appearing on tab select (normally used in modals)
    this.disableURL = this.tabContainer.hasAttribute('data-tabs-disable-url');

    this.state = {
      // Tab Settings
      activeTabID: '',
      transition: 150,
      initialPageLoad: true,
      // CSS Classes
      css: {
        animate: 'animate-in',
      },
      // Keyboard Keys
      keys: {
        end: 'End',
        home: 'Home',
        left: 'ArrowLeft',
        up: 'ArrowUp',
        right: 'ArrowRight',
        down: 'ArrowDown',
      },
      direction: {
        ArrowLeft: -1,
        ArrowRight: 1,
      },
    };

    this.onComponentLoaded();
  }

  onComponentLoaded() {
    this.bindEvents();

    // Set active tab from url or make first tab active
    if (this.tabButtons) {
      // Set each button's aria-controls attribute and select tab if aria-selected has already been set on the element
      Tabs.setAriaControlsByHref(this.tabButtons);
      // Check for active items set by the template
      const tabActive = [...this.tabButtons].find(
        (button) => button.getAttribute('aria-selected') === 'true',
      );

      if (window.location.hash && !this.disableURL) {
        this.selectTabByURLHash();
      } else if (tabActive) {
        // If a tab isn't hidden for some reason hide it
        this.tabPanels.forEach((tab) => {
          // eslint-disable-next-line no-param-reassign
          tab.hidden = true;
        });
        // Show aria-selected tab
        this.selectTab(tabActive);
      } else {
        this.selectFirstTab();
      }
    }

    // Set each external trigger button's aria-controls attribute
    if (this.tabTriggerLinks) {
      Tabs.setAriaControlsByHref(this.tabTriggerLinks);
    }
  }

  /**
   * @param {string}newTabId
   */
  unSelectActiveTab(newTabId) {
    // IF new tab ID is the current then don't transition out
    if (newTabId === this.state.activeTabID || !this.state.activeTabID) {
      return;
    }

    // Tab Content to deactivate
    const tabContent = this.tabContainer.querySelector(
      `#${this.state.activeTabID}`,
    );

    if (!tabContent) {
      return;
    }

    if (this.animate) {
      this.animateOut(tabContent);
    } else {
      tabContent.hidden = true;
    }

    const tab = this.tabContainer.querySelector(
      `a[href='#${this.state.activeTabID}']`,
    );

    tab.setAttribute('aria-selected', 'false');
    tab.setAttribute('tabindex', '-1');
  }

  selectTab(tab) {
    if (!tab) {
      return;
    }

    const tabContentId = tab.getAttribute('aria-controls');

    // Unselect currently active tab
    if (tabContentId) {
      this.unSelectActiveTab(tabContentId);
    }

    this.state.activeTabID = tabContentId;

    const linkedTab = this.tabContainer.querySelector(
      `a[href="${tab.getAttribute('href')}"][role="tab"]`,
    );

    // If an external button was used to trigger the tab, make sure active tab is marked active
    if (linkedTab) {
      linkedTab.setAttribute('aria-selected', 'true');
      linkedTab.removeAttribute('tabindex');
    }

    tab.setAttribute('aria-selected', 'true');
    tab.removeAttribute('tabindex');

    const tabContent = this.tabContainer.querySelector(`#${tabContentId}`);
    if (!tabContent) {
      return;
    }

    if (this.animate) {
      this.animateIn(tabContent);
    } else {
      tabContent.hidden = false;
    }

    if (this.state.initialPageLoad) {
      // On first load set the scroll to top to avoid scrolling to active section and header covering up tabs
      setTimeout(() => {
        window.scrollTo(0, 0);
      }, this.state.transition * 2);
    }

    // Dispatch tab selected event for the rest of the admin to hook into if needed
    // Trigger tab specific switch event
    this.tabList.dispatchEvent(
      new CustomEvent('switch', {
        detail: { tab: tab.getAttribute('href').replace('#', '') },
      }),
    );
    // Dispatch tab-changed event on the document
    document.dispatchEvent(new CustomEvent('wagtail:tab-changed'));

    // Set URL hash and browser history
    if (!this.disableURL) {
      this.setURLHash(tabContentId);
    }
  }

  /**
   * Fade Up and In animation
   * @param tabContent{HTMLElement}
   */
  animateIn(tabContent) {
    setTimeout(() => {
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = false;
      // Wait for hidden attribute to be applied then fade in
      setTimeout(() => {
        tabContent.classList.add(this.state.css.animate);
      }, this.state.transition);
    }, this.state.transition);
  }

  /**
   * Fade Down and Out by removing css class
   * @param tabContent{HTMLElement}
   */
  animateOut(tabContent) {
    // Wait element to transition out and then hide with hidden
    tabContent.classList.remove(this.state.css.animate);
    setTimeout(() => {
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = true;
    }, this.state.transition);
  }

  bindEvents() {
    if (this.tabButtons) {
      this.tabButtons.forEach((tab, index) => {
        tab.addEventListener('click', (e) => {
          e.preventDefault();
          this.selectTab(tab);
        });
        tab.addEventListener('keydown', this.keydownEventListener);
        // Set index of tab used in keyboard controls
        // eslint-disable-next-line no-param-reassign
        tab.index = index;
      });

      // Select previous or next tab using history
      window.addEventListener('popstate', (e) => {
        if (e.state && e.state.tabContent) {
          const tab = this.getTabElementByHref(`#${e.state.tabContent}`);
          if (tab) {
            this.selectTab(tab);
            tab.focus();
          }
        }
      });
    }

    if (this.tabTriggerLinks) {
      this.tabTriggerLinks.forEach((trigger) => {
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const tab = this.getTabElementByHref(trigger.getAttribute('href'));
          if (tab) {
            this.selectTab(tab);
            tab.focus();
          }
        });
      });
    }
  }

  /**
   * A query selector for selecting a tab element by it's href
   */
  getTabElementByHref(href) {
    return this.tabContainer.querySelector(`a[href="${href}"][role="tab"]`);
  }

  /**
   *  Handle keydown on tabs
   * @param {Event}event
   */
  keydownEventListener(event) {
    const keyPressed = event.key;
    const { keys } = this.state;

    switch (keyPressed) {
      case keys.left:
      case keys.right:
        this.switchTabOnArrowPress(event);
        break;
      case keys.end:
        event.preventDefault();
        this.focusLastTab();
        break;
      case keys.home:
        event.preventDefault();
        this.focusFirstTab();
        break;
      default:
        break;
    }
  }

  selectTabByURLHash() {
    if (window.location.hash) {
      const cleanedHash = window.location.hash.replace(/[^\w\-#]/g, '');
      const tab = this.getTabElementByHref(cleanedHash);
      if (tab) {
        this.selectTab(tab);
      } else {
        // The hash doesn't match a tab on the page then select first tab
        this.selectFirstTab();
      }
    }
  }

  /**
   * Set url to have tab an tab hash at the end
   */
  setURLHash(tabId) {
    if (
      !this.state.initialPageLoad &&
      (!window.history.state || window.history.state.tabContent !== tabId)
    ) {
      // Add a new history item to the stack
      window.history.pushState({ tabContent: tabId }, null, `#${tabId}`);
    }
    this.state.initialPageLoad = false;
  }

  // Either focus the next, previous, first, or last tab depending on key pressed
  switchTabOnArrowPress(event) {
    const pressed = event.key;
    const { direction } = this.state;
    const { keys } = this.state;
    const tabs = this.tabButtons;

    if (direction[pressed]) {
      const { target } = event;
      if (target.index !== undefined) {
        if (tabs[target.index + direction[pressed]]) {
          const tab = tabs[target.index + direction[pressed]];
          tab.focus();
          this.selectTab(tab);
        } else if (pressed === keys.left) {
          this.focusLastTab();
        } else if (pressed === keys.right) {
          this.focusFirstTab();
        }
      }
    }
  }

  focusFirstTab() {
    const tab = this.tabButtons[0];
    tab.focus();
    this.selectTab(tab);
  }

  focusLastTab() {
    const tab = this.tabButtons[this.tabButtons.length - 1];
    tab.focus();
    this.selectTab(tab);
  }

  selectFirstTab() {
    this.selectTab(this.tabButtons[0]);
    this.state.activeTabID = this.tabButtons[0].getAttribute('aria-controls');
  }

  /**
   *  Populate a list of links aria-controls attributes with their href value
   * @param links{HTMLAnchorElement[]}
   */
  static setAriaControlsByHref(links) {
    links.forEach((link) => {
      link.setAttribute(
        'aria-controls',
        link.getAttribute('href').replace('#', ''),
      );
    });
  }
}

export default Tabs;

export const initTabs = (tabs = document.querySelectorAll('[data-tabs]')) => {
  tabs.forEach((tabSet) => new Tabs(tabSet));

  // Dispatch tab-changed on window load
  if (tabs) {
    document.addEventListener('DOMContentLoaded', () => {
      document.dispatchEvent(new CustomEvent('wagtail:tab-changed'));
    });
  }
};
