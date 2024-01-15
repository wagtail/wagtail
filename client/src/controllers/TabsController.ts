import { Controller } from '@hotwired/stimulus';

export class TabsController extends Controller<HTMLElement> {
  static targets = ['tablist', 'tabcontent'];

  static values = {
    transition: { default: 150, type: Number },
    activeTabId: { default: '', type: String },
    disableURL: { default: false, type: Boolean },
    initialPageLoad: { default: true, type: Boolean },
    animate: { default: true, type: Boolean },
  };

  declare disableURLValue: boolean;
  declare initialPageLoadValue: boolean;
  declare activeTabIdValue: string;
  declare transitionValue: number;
  declare animateValue: boolean;

  declare tablist: HTMLDivElement;
  declare tabcontent: HTMLDivElement;

  declare tabsConstant;
  declare tabsButtons: NodeListOf<HTMLAnchorElement>;
  declare tabsPanel: NodeListOf<HTMLElement>;
  declare tabTriggerLinks: NodeListOf<HTMLElement>;
  declare tabList: HTMLElement;

  initialize() {
    this.tabsConstant = {
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

    this.tabsButtons = this.element.querySelectorAll('[role=tab]');
    this.tabsPanel = this.element.querySelectorAll('[role=tabpanel]');
    this.tabTriggerLinks = this.element.querySelectorAll('[data-tab-trigger]');
    this.tabList = this.element.querySelector('[role=tablist]') as HTMLElement;

    if (this.tabTriggerLinks) {
      this.tabTriggerLinks.forEach((trigger) => {
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const href = trigger.getAttribute('href') as string;
          const tab = this.getTabElementByHref(href) as HTMLElement;
          if (tab) {
            this.selectTab(tab);
            tab.focus();
          }
        });
      });
    }
  }

  // Populate a list of links aria-controls attributes with their href value
  setAriaControlByHref(tabLinks: NodeListOf<HTMLAnchorElement | HTMLElement>) {
    tabLinks.forEach((tabLink) => {
      const href = tabLink.getAttribute('href') as string;
      tabLink.setAttribute('aria-controls', href.replace('#', ''));
    });
  }

  connect() {
    if (this.tabsButtons) {
      this.setAriaControlByHref(this.tabsButtons);
      const tabActive = [...this.tabsButtons].find(
        (button) => button.getAttribute('aria-selected') === 'true',
      );

      if (window.location.hash && !this.disableURLValue) {
        this.selectTabByURLHash();
      } else if (tabActive) {
        this.tabsPanel.forEach((tab) => {
          // eslint-disable-next-line no-param-reassign
          tab.hidden = true;
        });
        this.selectTab(tabActive);
      } else {
        this.selectFirstTab();
      }
    }
    if (this.tabTriggerLinks) {
      this.setAriaControlByHref(this.tabTriggerLinks);
    }
  }

  selectTab(tab: HTMLElement) {
    if (!tab) {
      return;
    }
    const tabContentId = tab.getAttribute('aria-controls') as string;
    if (tabContentId) {
      this.unSelectActiveTab(tabContentId);
    }

    this.activeTabIdValue = tabContentId;

    const linkedTab = this.element.querySelector(
      `a[href="${tab.getAttribute('href')}"][role="tab"]`,
    );
    if (linkedTab) {
      linkedTab.setAttribute('aria-selected', 'true');
      linkedTab.removeAttribute('tabindex');
    }

    tab.setAttribute('aria-selected', 'true');
    tab.removeAttribute('tabindex');

    const tabContent = this.element.querySelector(
      `#${tabContentId}`,
    ) as HTMLElement;

    if (!tabContent) {
      return;
    }

    if (this.animateValue) {
      this.animateIn(tabContent);
    } else {
      tabContent.hidden = false;
    }

    if (this.initialPageLoadValue) {
      // On first load set the scroll to top to avoid scrolling to active section and header covering up tabs
      setTimeout(() => {
        window.scrollTo(0, 0);
      }, this.transitionValue * 2);
    }

    const href = tab.getAttribute('href') as string;
    this.tabList.dispatchEvent(
      new CustomEvent('switch', {
        detail: { tab: href.replace('#', '') },
      }),
    );
    // Dispatch tab-changed event on the document
    document.dispatchEvent(new CustomEvent('wagtail:tab-changed'));

    // Set URL hash and browser history
    if (!this.disableURLValue) {
      this.setURLHash(tabContentId);
    }
  }

  unSelectActiveTab(newTabId) {
    if (newTabId === this.activeTabIdValue || !this.activeTabIdValue) {
      return;
    }

    // Tab Content to deactivate
    const tabContent = this.element.querySelector(
      `#${this.activeTabIdValue}`,
    ) as HTMLElement;

    if (!tabContent) {
      return;
    }

    if (this.animateValue) {
      this.animateOut(tabContent);
    } else {
      tabContent.hidden = true;
    }

    const tab = this.element.querySelector(
      `a[href='#${this.activeTabIdValue}']`,
    ) as HTMLElement;

    tab.setAttribute('aria-selected', 'false');
    tab.setAttribute('tabindex', '-1');
  }

  getTabElementByHref(href: string) {
    return this.element.querySelector(`a[href="${href}"][role="tab"]`);
  }

  loadTabsFromHistory(event: PopStateEvent) {
    if (event.state && event.state.tabContent) {
      const tab = this.getTabElementByHref(
        `#${event.state.tabContent}`,
      ) as HTMLElement;
      if (tab) {
        this.selectTab(tab);
        tab.focus();
      }
    }
  }

  animateIn(tabContent: HTMLElement) {
    setTimeout(() => {
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = false;
      // Wait for hidden attribute to be applied then fade in
      setTimeout(() => {
        tabContent.classList.add(this.tabsConstant.css.animate);
      }, this.transitionValue);
    }, this.transitionValue);
  }

  animateOut(tabContent: HTMLElement) {
    // Wait element to transition out and then hide with hidden
    tabContent.classList.remove(this.tabsConstant.css.animate);
    setTimeout(() => {
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = true;
    }, this.transitionValue);
  }

  setURLHash(tabId: string) {
    if (
      !this.initialPageLoadValue &&
      (!window.history.state || window.history.state.tabContent !== tabId)
    ) {
      // Add a new history item to the stack
      window.history.pushState({ tabContent: tabId }, '', `#${tabId}`);
    }
    this.initialPageLoadValue = false;
  }

  selectTabByURLHash() {
    if (window.location.hash) {
      const cleanedHash = window.location.hash.replace(/[^\w\-#]/g, '');
      // Support linking straight to a tab, or to an element within a tab.
      const tabID = document
        .querySelector(cleanedHash)
        ?.closest('[role="tabpanel"]')
        ?.getAttribute('aria-labelledby') as string;
      const tab = document.getElementById(tabID);
      if (tab) {
        this.selectTab(tab);
      } else {
        // The hash doesn't match a tab on the page then select first tab
        this.selectFirstTab();
      }
    }
  }

  selectFirstTab() {
    this.selectTab(this.tabsButtons[0]);
    this.activeTabIdValue = this.tabsButtons[0].getAttribute(
      'aria-controls',
    ) as string;
  }

  // func bindEvents listening for click events
  // on tab title
  changeTab(event: MouseEvent) {
    event.preventDefault();
    const targetElement = event.target as HTMLElement;
    this.selectTab(targetElement);
  }

  switchTabOnArrowPress(event: KeyboardEvent) {
    const keyPressed = event.key;
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const index = event.target.index;
    const { direction, keys } = this.tabsConstant;

    if (direction[keyPressed]) {
      if (index !== undefined) {
        if (this.tabsButtons[index + direction[keyPressed]]) {
          const tab = this.tabsButtons[
            index + direction[keyPressed]
          ] as HTMLAnchorElement;
          tab.focus();
          this.selectTab(tab);
        } else if (keyPressed === keys.left) {
          const lastTab = this.tabsButtons[this.tabsButtons.length - 1];
          this.focusTab(lastTab);
        } else if (keyPressed === keys.right) {
          const firstTab = this.tabsButtons[0];
          this.focusTab(firstTab);
        }
      }
    }
  }

  focusTab(tab: HTMLAnchorElement) {
    tab.focus();
    this.selectTab(tab);
  }
}
