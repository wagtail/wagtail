/** Example Markup:
 <div class="w-tabs" data-tabs data-tabs-animate>
 <div class="w-tabs__wrapper w-overflow-x-auto u-scrollbar-thin">
 <div role="tablist" class="w-tabs__list">
 {% include 'wagtailadmin/shared/tabs/tab_nav_link.html' with tab_id='slug' title='Tab Title' %}
 </div>
 <!-- Tab Content -->
 <section id="tab-{{ tab_id }}" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-label-{{ tab_id }}" hidden>
 {{ content }}
 </section>
 </div>
 </div>
 */
class Tabs {
  constructor(node) {
    this.tabContainer = node;
    this.tabButtons = this.tabContainer.querySelectorAll('[role="tab"]');
    this.tabList = this.tabContainer.querySelector('[role="tablist"]');
    this.tabPanels = this.tabContainer.querySelectorAll('[role="tabpanel"]');

    // Tab Options - Add these data attributes along side the data-tabs attribute
    // Use this to enable fade-in animations on tab select
    this.animate = this.tabContainer.hasAttribute('data-tabs-animate');
    // Disable url hash from appearing on tab select (normally used in modals)
    this.disableUrl = this.tabContainer.hasAttribute('data-tabs-disable-url');

    this.state = {
      // Tab Settings
      activeTabID: '',
      transition: 150,
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
        enter: 'Enter',
        space: ' ',
        // Key names specific for Edge
        edgeBrowser: {
          left: 'Left',
          right: 'Right',
          down: 'Down',
          up: 'Up',
        },
      },
      direction: {
        ArrowLeft: -1,
        Left: -1,
        ArrowUp: -1,
        Up: -1,
        ArrowRight: 1,
        Right: 1,
        ArrowDown: 1,
        Down: 1,
      },
    };

    this.onComponentLoaded();
  }

  onComponentLoaded() {
    this.bindEvents();

    // Set active tab from url or make first tab active
    if (this.tabButtons) {
      // Set each button's aria-controls attribute and select tab if aria-selected has already been set on the element
      this.tabButtons.forEach((button) => {
        button.setAttribute(
          'aria-controls',
          button.getAttribute('href').replace('#', ''),
        );
      });

      // Check for active items set by the template
      const tabActive = [...this.tabButtons].find(
        (button) => button.getAttribute('aria-selected') === 'true',
      );

      if (window.location.hash && !this.disableUrl) {
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

  /**
   * @param {HTMLElement}tab
   */
  selectTab(tab) {
    if (tab) {
      const tabContentId = tab.getAttribute('aria-controls');

      // Unselect currently active tab
      if (tabContentId) {
        this.unSelectActiveTab(tabContentId);
      }

      this.state.activeTabID = tabContentId;

      tab.setAttribute('aria-selected', true);
      tab.removeAttribute('tabindex');
      const tabContent = this.tabContainer.querySelector(`#${tabContentId}`);

      if (this.animate) {
        this.animateIn(tabContent);
      } else {
        tabContent.hidden = false;
      }

      // Dispatch tab selected event for the rest of the admin to hook into if needed
      // Trigger tab specific switch event
      this.tabList.dispatchEvent(
        new CustomEvent('switch', { detail: { tab: tab.dataset.tab } }),
      );
      // Dispatch tab-changed event on the document
      document.dispatchEvent(new CustomEvent('tab-changed'));

      // Set url hash
      if (!this.disableUrl) {
        this.setUrlHash(tab.getAttribute('href'));
      }
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
    if (!this.tabButtons) {
      return;
    }

    this.tabButtons.forEach((tab, index) => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        this.selectTab(tab);
      });
      tab.addEventListener('keydown', this.keydownEventListener);
      tab.addEventListener('keyup', this.keyupEventListener);
      // Set index of tab used in keyboard controls
      // eslint-disable-next-line no-param-reassign
      tab.index = index;
    });
  }

  /**
   *  Handle keydown on tabs
   * @param {Event}event
   */
  keydownEventListener(event) {
    const keyPressed = event.key;
    const { keys } = this.state;

    switch (keyPressed) {
      case keys.end:
        event.preventDefault();
        // Activate last tab
        this.focusLastTab();
        break;
      case keys.home:
        event.preventDefault();
        // Activate first tab
        this.focusFirstTab();
        break;
      // Up and down are here in keydown
      // To prevent page scroll
      case keys.edgeBrowser.up:
      case keys.edgeBrowser.down:
      case keys.up:
      case keys.down:
        this.determineOrientation(event);
        break;
      default:
        break;
    }
  }

  /**
   *  Handle keyup on tabs
   * @param {Event}event
   */
  keyupEventListener(event) {
    const keyPressed = event.key;
    const { keys } = this.state;

    switch (keyPressed) {
      case keys.edgeBrowser.left:
      case keys.edgeBrowser.right:
      case keys.left:
      case keys.right:
        this.determineOrientation(event);
        break;
      case keys.enter:
      case keys.space:
        this.selectTab(event.target);
        break;
      default:
        break;
    }
  }

  determineOrientation(event) {
    const key = event.key;
    const { keys } = this.state;
    let proceed = false;

    if (this.vertical) {
      if (
        key === keys.up ||
        key === keys.edgeBrowser.up ||
        key === keys.down ||
        key === keys.edgeBrowser.down
      ) {
        event.preventDefault();
        proceed = true;
      }
    } else if (
      key === keys.left ||
      key === keys.edgeBrowser.left ||
      key === keys.right ||
      key === keys.edgeBrowser.right
    ) {
      proceed = true;
    }

    if (proceed) {
      this.switchTabOnArrowPress(event);
    }
  }

  selectTabByURLHash() {
    // Select tab by hash
    if (window.location.hash) {
      const cleanedHash = window.location.hash.replace(/[^\w\-#]/g, '');
      const tab = this.tabContainer.querySelector(
        `a[href="${cleanedHash}"][data-tab]`,
      );
      if (tab) {
        this.selectTab(tab);
      } else {
        // The hash doesn't match a tab on the page then select first tab
        this.selectFirstTab();
      }
    }
  }

  /**
   *
   * @param {string}hash
   */
  setUrlHash(hash) {
    window.history.replaceState(null, null, hash);
  }

  // Either focus the next, previous, first, or last tab depending on key pressed
  switchTabOnArrowPress(event) {
    const pressed = event.key;
    const { direction } = this.state;
    const { keys } = this.state;
    const tabs = this.tabButtons;

    if (direction[pressed]) {
      const target = event.target;
      if (target.index !== undefined) {
        if (tabs[target.index + direction[pressed]]) {
          tabs[target.index + direction[pressed]].focus();
        } else if (pressed === keys.left || pressed === keys.up) {
          this.focusLastTab();
        } else if (pressed === keys.right || pressed === keys.down) {
          this.focusFirstTab();
        }
      }
    }
  }

  focusFirstTab() {
    this.tabButtons[0].focus();
  }

  focusLastTab() {
    this.tabButtons[this.tabButtons.length - 1].focus();
  }

  // Handle params are passed through the url
  handleParams() {
    // TODO: update to select correct element on page load depending on href
    this.tabName = window.location.hash.substring(1);
  }

  selectFirstTab() {
    this.selectTab(this.tabButtons[0]);
    this.state.activeTabID = this.tabButtons[0].getAttribute('aria-controls');
  }
}

export default Tabs;

export const initTabs = (tabs = document.querySelectorAll('[data-tabs]')) => {
  tabs.forEach((tabSet) => new Tabs(tabSet));
};
