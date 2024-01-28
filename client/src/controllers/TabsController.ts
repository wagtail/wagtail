/* eslint-disable no-shadow */
import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

interface IndexedEventTarget extends EventTarget {
  index: number;
}

interface TabLink extends HTMLAnchorElement {
  index: number;
}

enum Keys {
  Left = 'ArrowLeft',
  Right = 'ArrowRight',
  Home = 'Home',
  End = 'End',
}

enum KeyWeight {
  ArrowLeft = -1,
  ArrowRight = 1,
}

/**
 * @example - creating a simple tabs interface
 * <div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-active-value="" data-w-tabs-animate-class="animate-in">
 *   <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
 *       <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab"
 *          tabindex="-1" data-action="click->w-tabs#handleTabChange:prevent keydown->w-tabs#handleKeydown" data-w-tabs-target="label">
 *         Tab 1
 *       </a>
 *       <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
 *          data-action="click->w-tabs#handleTabChange:prevent keydown->w-tabs#handleKeydown" data-w-tabs-target="label">
 *         Tab 2
 *       </a>
 *   </div>
 *
 *   <div class="tab-content tab-content--comments-enabled">
 *       <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
 *           tab-1
 *       </section>
 *       <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
 *           tab-2
 *       </section>
 *   </div>
 * </div>
 */

export class TabsController extends Controller<HTMLDivElement> {
  static targets = ['list', 'trigger', 'label', 'panel'];

  static classes = ['animate'];

  static values = {
    transition: { default: 150, type: Number },
    active: { default: '', type: String },
    disable: { default: false, type: Boolean },
    animate: { default: true, type: Boolean },
  };

  declare readonly animateClass: string;

  declare listTarget: HTMLDivElement;
  declare triggerTargets: HTMLAnchorElement[];
  declare labelTargets: HTMLAnchorElement[];
  declare panelTargets: HTMLElement[];

  declare disableValue: boolean;
  declare activeValue: string;
  declare transitionValue: number;
  declare animateValue: boolean;

  activeValueChanged(currentValue: string, previousValue: string) {
    if (previousValue) {
      this.hideTabContent(previousValue);
    }

    const tab = this.getTabLabelByHref(currentValue);
    if (tab) {
      tab.setAttribute('aria-selected', 'true');
      tab.removeAttribute('tabindex');
    }

    const tabContent = this.getTabPanelByHref(currentValue);

    if (tabContent) {
      if (this.animateValue) {
        this.animateIn(tabContent);
      } else {
        tabContent.hidden = false;
      }

      this.listTarget.dispatchEvent(
        new CustomEvent('switch', {
          detail: { tab: tab?.getAttribute('href')?.replace('#', '') },
        }),
      );
      this.dispatch('changed', {
        cancelable: false,
        detail: { to: previousValue },
      });
      // document.dispatchEvent(new CustomEvent('wagtail:tab-changed'));

      if (!this.disableValue) {
        this.setURLHash(currentValue);
      }
    }
  }

  connect() {
    this.validate();

    debounce(() => {
      window.scrollTo(0, 0);
    }, this.transitionValue * 2);

    this.setAriaControls(this.labelTargets);
    this.setTabLabelIndex();

    const activeTab = this.labelTargets.find(
      (button) => button.getAttribute('aria-selected') === 'true',
    );

    this.panelTargets.forEach((tab) => {
      // eslint-disable-next-line no-param-reassign
      tab.hidden = true;
    });

    if (window.location.hash && !this.disableValue) {
      this.setTabByURLHash();
    } else if (activeTab) {
      this.activeValue = activeTab.getAttribute('aria-controls') as string;
    } else {
      this.selectFirstTab();
    }

    this.setAriaControls(this.triggerTargets);
  }

  handleTriggerLinks(event: MouseEvent) {
    const href = (event.target as HTMLAnchorElement).getAttribute(
      'href',
    ) as string;
    const tab = this.getTabLabelByHref(href);
    if (tab) {
      this.activeValue = href.replace('#', '');
      tab.focus();
    }
  }

  handleTabChange(event: MouseEvent) {
    const tabId = (event.target as HTMLElement).getAttribute(
      'aria-controls',
    ) as string;
    this.activeValue = tabId;
    // this.selectTab(targetElement);
  }

  getTabLabelByHref(tabId: string): HTMLElement | undefined {
    return this.labelTargets.find(
      (tab) => tab.getAttribute('aria-controls') === tabId,
    );
  }

  getTabPanelByHref(tabId: string): HTMLElement | undefined {
    return this.panelTargets.find((tab) => tab.getAttribute('id') === tabId);
  }

  setAriaControls(tabLinks: HTMLAnchorElement[]) {
    tabLinks.forEach((tabLink) => {
      const href = tabLink.getAttribute('href') as string;
      tabLink.setAttribute('aria-controls', href.replace('#', ''));
    });
  }

  setTabLabelIndex() {
    (this.labelTargets as TabLink[]).forEach((label, index) => {
      // eslint-disable-next-line no-param-reassign
      label.index = index;
    });
  }

  setURLHash(tabId: string) {
    if (!window.history.state || window.history.state.tabContent !== tabId) {
      // Add a new history item to the stack
      window.history.pushState({ tabContent: tabId }, '', `#${tabId}`);
    }
  }

  setTabByURLHash() {
    if (window.location.hash) {
      const cleanedHash = window.location.hash
        .replace(/[^\w\-#]/g, '')
        .replace('#', '');
      if (cleanedHash) {
        this.activeValue = cleanedHash;
        // this.selectTab(tab);
      } else {
        // The hash doesn't match a tab on the page then select first tab
        this.selectFirstTab();
      }
    }
  }

  selectFirstTab() {
    const href = this.labelTargets[0].getAttribute('aria-controls') as string;
    this.activeValue = href;
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

  hideTabContent(tabId: string) {
    if (tabId === this.activeValue || !this.activeValue) {
      return;
    }

    const tabContent = this.getTabPanelByHref(tabId);
    if (!tabContent) {
      return;
    }
    if (this.animateValue) {
      this.animateOut(tabContent);
    } else {
      tabContent.hidden = true;
    }

    const tab = this.getTabLabelByHref(tabId);
    if (!tab) {
      return;
    }
    tab.setAttribute('aria-selected', 'false');
    tab.setAttribute('tabindex', '-1');
  }

  handleKeydown(event: KeyboardEvent) {
    const keyPressed = event.key;

    switch (keyPressed) {
      case Keys.Left:
      case Keys.Right:
        this.switchTabOnArrowPress(event);
        break;
      case Keys.End:
        event.preventDefault();
        this.focusLastTab();
        break;
      case Keys.Home:
        event.preventDefault();
        this.focusFirstTab();
        break;
      default:
        break;
    }
  }

  switchTabOnArrowPress(event) {
    const pressed = event.key;
    if (!event.target) {
      return;
    }

    let direction: number = 0;
    if (pressed === Keys.Left) {
      direction = KeyWeight.ArrowLeft;
    }
    if (pressed === Keys.Right) {
      direction = KeyWeight.ArrowRight;
    }

    const tabIndex = (event.target as IndexedEventTarget).index;
    const tab = this.labelTargets[tabIndex + direction];
    if (tabIndex !== undefined) {
      if (tab) {
        this.activeValue = tab.getAttribute('aria-controls') as string;
        tab.focus();
      } else if (pressed === Keys.Left) {
        this.focusLastTab();
      } else if (pressed === Keys.Right) {
        this.focusFirstTab();
      }
    }
  }

  focusFirstTab() {
    const tab = this.labelTargets[0];
    this.activeValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  focusLastTab() {
    const tab = this.labelTargets[this.labelTargets.length - 1];
    this.activeValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  loadHistory(event: PopStateEvent) {
    if (event.state && event.state.tabContent) {
      const tab = this.getTabLabelByHref(event.state.tabContent);
      if (tab) {
        this.activeValue = event.state.tabContent;
        tab.focus();
      }
    }
  }

  validate() {
    this.labelTargets.forEach((label, idx) => {
      const panel = this.panelTargets[idx];
      if (label.getAttribute('role') !== 'tab') {
        // eslint-disable-next-line no-console
        console.warn(
          label,
          "this element does not have role='tab' aria attribute",
        );
      }
      if (panel.getAttribute('role') !== 'tabpanel') {
        // eslint-disable-next-line no-console
        console.warn(
          panel,
          "this element does not have role='tabpanel' aria attribute",
        );
      }
      if (panel.getAttribute('aria-labelledby') !== label.id) {
        // eslint-disable-next-line no-console
        console.warn(panel, 'this element does not have aria-labelledby');
      }
      if (this.listTarget.getAttribute('role') !== 'tablist') {
        // eslint-disable-next-line no-console
        console.warn(
          this.listTarget,
          "this element does not have role='tablist' aria attribute",
        );
      }
    });
  }
}
