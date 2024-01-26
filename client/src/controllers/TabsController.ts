/* eslint-disable no-shadow */
import { Controller } from '@hotwired/stimulus';

enum ArrowKeys {
  Left = "ArrowLeft",
  Right = "ArrowRight"
}

enum KeyWeight {
  ArrowLeft = -1,
  ArrowRight = 1
}

export class TabsController extends Controller<HTMLDivElement> {
  static targets = ['list', 'trigger', 'label', 'panel'];

  static classes = ['animate']

  static values = {
    transition: { default: 150, type: Number },
    active: { default: '', type: String },
    disable: { default: false, type: Boolean },
    animate: { default: true, type: Boolean },
  };

  declare animateClass;

  declare listTarget: HTMLDivElement;
  declare triggerTargets: HTMLElement[];
  declare labelTargets: HTMLAnchorElement[];
  declare panelTargets: HTMLElement[];

  declare disableValue: boolean;
  declare activeValue: string;
  declare transitionValue: number;
  declare animateValue: boolean;

  // Populate a list of links aria-controls attributes with their href value
  setAriaControlByHref(tabLinks: HTMLAnchorElement[] | HTMLElement[]) {
    tabLinks.forEach((tabLink) => {
      const href = tabLink.getAttribute('href') as string;
      tabLink.setAttribute('aria-controls', href.replace('#', ''));
    });
  }

  connect() {
    setTimeout(() => {
      window.scrollTo(0, 0);
    }, this.transitionValue * 2);

    this.setAriaControlByHref(this.labelTargets);
    const tabActive = [...this.labelTargets].find(
      (button) => button.getAttribute('aria-selected') === 'true',
    );

    this.panelTargets.forEach((tab) => {
      // eslint-disable-next-line no-param-reassign
      tab.hidden = true;
    });

    if (window.location.hash && !this.disableValue) {
      this.selectTabByURLHash();
    } else if (tabActive) {
      this.selectTab(tabActive);
    } else {
      this.selectFirstTab();
    }

    this.setAriaControlByHref(this.triggerTargets);
  }

  selectTab(tab: HTMLElement) {
    if (!tab) {
      return;
    }
    const tabContentId = tab.getAttribute('aria-controls') as string;
    if (tabContentId) {
      this.unSelectActiveTab(tabContentId);
    }

    this.activeValue = tabContentId;

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

    const href = tab.getAttribute('href') as string;
    this.listTarget.dispatchEvent(
      new CustomEvent('switch', {
        detail: { tab: href.replace('#', '') },
      }),
    );
    // Dispatch tab-changed event on the document
    document.dispatchEvent(new CustomEvent('wagtail:tab-changed'));

    // Set URL hash and browser history
    if (!this.disableValue) {
      this.setURLHash(tabContentId);
    }
  }

  unSelectActiveTab(newTabId: string) {
    if (newTabId === this.activeValue || !this.activeValue) {
      return;
    }

    // Tab Content to deactivate
    const tabContent = this.element.querySelector(
      `#${this.activeValue}`,
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
      `a[href='#${this.activeValue}']`,
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
        tabContent.classList.add(this.animateClass);
      }, this.transitionValue);
    }, this.transitionValue);
  }

  animateOut(tabContent: HTMLElement) {
    // Wait element to transition out and then hide with hidden
    tabContent.classList.remove(this.animateClass);
    setTimeout(() => {
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = true;
    }, this.transitionValue);
  }

  setURLHash(tabId: string) {
    if (!window.history.state || window.history.state.tabContent !== tabId) {
      // Add a new history item to the stack
      window.history.pushState({ tabContent: tabId }, '', `#${tabId}`);
    }
  }

  selectTabByURLHash() {
    const cleanedHash = window.location.hash.replace(/[^\w\-#]/g, '');
    // Support linking straight to a tab, or to an element within a tab.
    const tab = this.element.querySelector(`[aria-controls=${cleanedHash.replace("#", "")}]`) as HTMLElement
    if (tab) {
      this.selectTab(tab);
    } else {
      // The hash doesn't match a tab on the page then select first tab
      this.selectFirstTab();
    }
  }

  selectFirstTab() {
    this.selectTab(this.labelTargets[0]);
    this.activeValue = this.labelTargets[0].getAttribute(
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
    let weight = 0;

    if (keyPressed === ArrowKeys.Left) {
      weight = KeyWeight.ArrowLeft
    }

    if (keyPressed === ArrowKeys.Right) {
      weight = KeyWeight.ArrowRight
    }

    if (index === undefined) {
      return;
    }
    
    if (this.labelTargets[index + weight]) {
      const tab = this.labelTargets[
        index + weight
      ] as HTMLAnchorElement;
      tab.focus();
      this.selectTab(tab);
    } else if (keyPressed === ArrowKeys.Left) {
      const lastTab = this.labelTargets[this.labelTargets.length - 1];
      this.focusTab(lastTab);
    } else if (keyPressed === ArrowKeys.Right) {
      const firstTab = this.labelTargets[0];
      this.focusTab(firstTab);
    }
  }


  focusTab(tab: HTMLAnchorElement) {
    this.selectTab(tab);
    tab.focus();
  }
}