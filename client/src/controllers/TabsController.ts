/* eslint-disable no-shadow */
import { Controller } from '@hotwired/stimulus';
import { debounce } from '../utils/debounce';

interface IndexedEventTarget extends EventTarget {
  index: number;
}

interface TabLink extends HTMLAnchorElement {
  index: number;
}

/**
 * @example - creating a simple tabs interface
 *<div class="w-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadHistory" data-w-tabs-selected-value="" data-w-tabs-selected-class="animate-in">
 *    <div class="w-tabs__list" role="tablist" data-w-tabs-target="list">
 *        <a id="tab-label-tab-1" href="#tab-tab-1" class="w-tabs__tab" role="tab" tabindex="-1"
 *           data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
 *            Tab 1
 *        </a>
 *        <a id="tab-label-tab-2" href="#tab-tab-2" class="w-tabs__tab" role="tab"
 *           data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
 *            Tab 2
 *        </a>
 *        <a id="tab-label-tab-3" href="#tab-tab-3" class="w-tabs__tab" role="tab"
 *           data-action="click->w-tabs#handleTabChange:prevent keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast" data-w-tabs-target="label">
 *            Tab 3
 *        </a>
 *    </div>
 *    <div class="tab-content tab-content--comments-enabled">
 *        <section id="tab-tab-1" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-1" data-w-tabs-target="panel">
 *            tab-1
 *        </section>
 *        <section id="tab-tab-2" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-2" data-w-tabs-target="panel">
 *            tab-2
 *        </section>
 *        <section id="tab-tab-3" class="w-tabs__panel " role="tabpanel" aria-labelledby="tab-label-tab-3" data-w-tabs-target="panel">
 *            tab-3
 *        </section>
 *    </div>
 *</div>
 */

export class TabsController extends Controller<HTMLDivElement> {
  static targets = ['list', 'trigger', 'label', 'panel'];

  static classes = ['selected'];

  static values = {
    transition: { default: 150, type: Number },
    selected: { default: '', type: String },
    syncURLHash: { default: false, type: Boolean },
    animate: { default: true, type: Boolean },
  };

  declare readonly selectedClasses: string;

  declare listTarget: HTMLDivElement;
  declare triggerTargets: HTMLAnchorElement[];
  declare labelTargets: HTMLAnchorElement[];
  declare panelTargets: HTMLElement[];

  declare syncURLHashValue: boolean;
  declare selectedValue: string;
  declare transitionValue: number;
  declare animateValue: boolean;

  connect() {
    this.validate();

    debounce(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, this.transitionValue * 2);

    this.setAriaControls(this.labelTargets);
    this.setTabLabelIndex();

    const activeTab = this.labelTargets.find(
      (button) =>
        button.getAttribute('aria-selected') === 'true' ||
        button.getAttribute('aria-controls') === this.selectedValue,
    );

    if (this.selectedClasses !== '' && activeTab) {
      activeTab.setAttribute('aria-selected', 'true');
      activeTab.removeAttribute('tabindex');
    }

    this.panelTargets.forEach((tab) => {
      // eslint-disable-next-line no-param-reassign
      tab.hidden = true;
    });

    // console.log(this.selectedValue ? "hello": "bye!", "selected")
    // console.log(activeTab)
    if (window.location.hash && !this.syncURLHashValue) {
      this.setTabByURLHash();
    } else if (activeTab) {
      this.selectedValue = activeTab.getAttribute('aria-controls') as string;
    } else {
      this.selectFirstTab();
    }

    this.setAriaControls(this.triggerTargets);
  }

  selectedValueChanged(currentValue: string, previousValue: string) {
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

      this.dispatch('switch', {
        detail: { tab: tab?.getAttribute('href')?.replace('#', '') },
        target: this.listTarget,
      });

      this.dispatch('selected', {
        cancelable: false,
        detail: { selected: currentValue },
      });

      if (!this.syncURLHashValue) {
        this.setURLHash(currentValue);
      }
    }
  }

  handleTriggerLinks(event: MouseEvent) {
    const href = (event.target as HTMLAnchorElement).getAttribute(
      'href',
    ) as string;
    const tab = this.getTabLabelByHref(href);
    if (tab) {
      this.selectedValue = href.replace('#', '');
      tab.focus();
    }
  }

  handleTabChange(event: MouseEvent) {
    const tabId = (event.target as HTMLElement).getAttribute(
      'aria-controls',
    ) as string;
    this.selectedValue = tabId;
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
        this.selectedValue = cleanedHash;
      } else {
        // The hash doesn't match a tab on the page then select first tab
        this.selectFirstTab();
      }
    }
  }

  selectFirstTab() {
    const href = this.labelTargets[0].getAttribute('aria-controls') as string;
    this.selectedValue = href;
  }

  animateIn(tabContent: HTMLElement) {
    debounce(() => {
      tabContent.classList.add(...this.selectedClasses);
    }, this.transitionValue || null)().then(() => {
      // Wait for hidden attribute to be applied then fade in
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = false;
    });
  }

  animateOut(tabContent: HTMLElement) {
    debounce(() => {
      tabContent.classList.remove(...this.selectedClasses);
    }, this.transitionValue || null)().then(() => {
      // Wait element to transition out and then hide with hidden
      // eslint-disable-next-line no-param-reassign
      tabContent.hidden = true;
    });
  }

  hideTabContent(tabId: string) {
    if (tabId === this.selectedValue || !this.selectedValue) {
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

  selectNext(event: Event) {
    const tabIndex = (event.target as IndexedEventTarget).index;
    const tab = this.labelTargets[tabIndex + 1];
    if (!tab) {
      return;
    }
    this.selectedValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  selectPrevious(event: Event) {
    const tabIndex = (event.target as IndexedEventTarget).index;
    const tab = this.labelTargets[tabIndex + -1];
    if (!tab) {
      return;
    }
    this.selectedValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  selectFirst() {
    const tab = this.labelTargets[0];
    this.selectedValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  selectLast() {
    const tab = this.labelTargets[this.labelTargets.length - 1];
    this.selectedValue = tab.getAttribute('aria-controls') as string;
    tab.focus();
  }

  loadHistory(event: PopStateEvent) {
    if (event.state && event.state.tabContent) {
      const tab = this.getTabLabelByHref(event.state.tabContent);
      if (tab) {
        this.selectedValue = event.state.tabContent;
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
