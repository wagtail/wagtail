/* eslint no-param-reassign: ["error", {  "ignorePropertyModificationsFor": ["hidden"] }] */

import { Controller } from '@hotwired/stimulus';

import { getElementByContentPath } from '../utils/contentPath';
import { debounce } from '../utils/debounce';
import { after } from '../utils/after';
import { noop } from '../utils/noop';

const immediatePromiseLike = <T>(value: T) =>
  ({
    then: (resolve: (value: T) => void) => {
      resolve(value);
    },
    catch: noop,
    finally: noop,
  }) as Promise<T>;

/**
 * Adds the ability for the controlled elements to behave as selectable tabs
 * where one panel will be active at a time.
 *
 * @description
 * - All tabs, triggers and tab panels must be nested in an element within the scope of the controller.
 * - All tab (buttons/links) need the `role="tab"` attribute and either a `href` with the tab content `id` with the target `tab` or a `aria-controls` set to a target `tab`.
 * - Tab (buttons/links as trigger targets) are those that are wrapped in an element with the `role="tablist"` attribute.
 * - Tab panels must have the `role="tabpanel"` attribute and and `id` attribute that matches the `href` of the tab link with the target 'panel'.
 * - Use the target 'trigger' on an Anchor link and set the `href` to the `id` of the tab you would like to trigger or use action params.
 *
 * @example - Basic tabs (with initial selection)
 * ```html
 * <div data-controller="w-tabs">
 *   <div role="tablist">
 *     <a id="edit-tab-label" href="#panel-edit" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">Edit</a>
 *     <a id="sett-tab-label" href="#panel-sett" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent" aria-selected="true">Settings</a>
 *   </div>
 *   <div class="tab-content">
 *     <section id="panel-edit" role="tabpanel" aria-labelledby="edit-tab-label" data-w-tabs-target="panel">Edit</section>
 *     <section id="panel-sett" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">Settings</section>
 *    </div>
 * </div>
 * ```
 *
 * @example - Full tabs with class changes, history/location handling, keyboard controls & extra trigger
 * ```html
 * <div data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-active-class="animate-in" data-w-tabs-use-location-value="true">
 *   <div role="tablist" data-action="keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast">
 *     <a id="tab-1" href="#panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">Tab 1</a>
 *     <a id="tab-2" href="#panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">Tab 2</a>
 *   </div>
 *   <div class="tab-content">
 *     <section id="panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">
 *       Tab 1 content
 *     </section>
 *     <section id="panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
 *       Tab 2 content
 *     </section>
 *   </div>
 *   <button type="button" data-action="w-tabs#select" data-w-tabs-id-param="panel-1" data-w-tabs-target="trigger">Extra trigger for Tab 1</button>
 * </div>
 * ```
 */
export class TabsController extends Controller {
  static classes = ['active'];

  static targets = ['panel', 'trigger'];

  static values = {
    activePanelId: { default: '', type: String },
    transition: { default: 0, type: Number },
    useLocation: { default: false, type: Boolean },
  };

  /** The `id` of the panel (not the tab/trigger) that's currently active. */
  declare activePanelIdValue: string | null;

  /** Classes to add to the panel content when active. */
  declare readonly activeClasses: string[];
  /** Tab content panels, with role='tabpanel', showing the content for each tab. */
  declare readonly panelTargets: HTMLElement[];
  /** The time, in milliseconds, for the tab content to transition in and out. If zero or negative, no transition will take place. */
  declare readonly transitionValue: number;
  /** Any elements within the controller's scope that may select a specific panel. */
  declare readonly triggerTargets: (HTMLButtonElement | HTMLAnchorElement)[];
  /** If true, the selected tab will sync with the URL hash and the URL hash will be checked on load for a selected tab panel (or panel contents). */
  declare readonly useLocationValue: boolean;

  /** The key for reading/applying history state if `locationSync` is enabled, based on the controller's identifier. */
  historyStateKey: string = 'tabs-panel-id';
  /** Trigger elements that are the primary tabs, with role='tab' within the role='tablist'. */
  tabs: (HTMLButtonElement | HTMLAnchorElement)[] = [];

  /**
   * Validate & clean targets, set the initial active panel,
   * hide any non active panels then dispatch ready.
   *
   * Once ready, allow for targets to change and reset the tabs & validation.
   *
   * @fires TabsController#ready - When the controller is ready and has set the initial active panel.
   * @event TabsController#ready
   * @type {CustomEvent}
   * @property {Object} detail
   * @property {string} detail.current - The id of the currently active panel.
   * @property {string} name - `w-tabs:update` (depending on the controller's identifier)
   * @property {HTMLElement} target - The controller's element.
   */
  connect() {
    this.historyStateKey = `${this.identifier}-panel-id`;
    this.tabs = this.validatedTabs;

    const initialPanelId = this.setInitialPanel();

    // Clean up the DOM, ensure any initially non-active panels are hidden

    this.panelTargets
      .filter(({ id }) => id !== initialPanelId)
      .forEach((target) => {
        target.hidden = true;
      });

    // Dispatch ready event with the initial panel id

    this.dispatch('ready', {
      cancelable: false,
      detail: { current: initialPanelId },
    });

    // Once ready, allow target changed callbacks to reset tabs

    const resetTabs = debounce(() => {
      this.tabs = this.validatedTabs;
    }, 10);

    this.panelTargetConnected = resetTabs;
    this.panelTargetDisconnected = resetTabs;
    this.triggerTargetConnected = resetTabs;
    this.triggerTargetDisconnected = resetTabs;

    // Ensure the syncLocation runs only the second time so we do not update the URL/history on load
    this.syncLocation = after(this.syncLocation.bind(this), 1);
  }

  /**
   * Whenever the active panel has changed, handle transitions and selection from the current
   * to the new panels.
   *
   * @fires TabsController#selected - When a new panel is about to be active, fires on the triggers/tab for that panel.
   * @event TabsController#selected
   * @type {CustomEvent}
   * @property {Object} detail
   * @property {string} detail.current - The id of the currently active panel.
   * @property {string} detail.previous - The id of the previously active panel.
   * @property {HTMLElement} detail.tabs - The controller's element.
   * @property {string} name - `w-tabs:selected` (depending on the controller's identifier)
   * @property {HTMLElement} target - The trigger/tab that is now selected.
   *
   * @fires TabsController#changed - When a new panel is active, fires on the panel that is now active.
   * @event TabsController#changed
   * @type {CustomEvent}
   * @property {Object} detail
   * @property {string} detail.current - The id of the currently active panel.
   * @property {string} detail.previous - The id of the previously active panel.
   * @property {HTMLElement} detail.tabs - The controller's element.
   * @property {string} name - `w-tabs:changed` (depending on the controller's identifier)
   * @property {HTMLElement} target - The panel that is now active.
   */
  activePanelIdValueChanged(currentPanelId: string, previousPanelId: string) {
    if (this.tabs.length === 0) return; // tabs are not ready or have been set up incorrectly
    if (!currentPanelId) return; // initial value not yet set
    if (currentPanelId === previousPanelId) return; // do not do anything if there is no change

    const panelTargets = this.panelTargets;

    const panel = panelTargets.find(({ id }) => id === currentPanelId);

    if (!panel) return;

    // Deactivate currently active panel & set all associated triggers (not just tabs) as not selected
    // Active newly active panel & set associated triggers (not just tabs) as selected, dispatch events
    this.triggerTargets.forEach((target) => {
      if (target.getAttribute('aria-controls') !== currentPanelId) {
        target.removeAttribute('aria-selected');
        target.setAttribute('tabindex', '-1');
        return;
      }
      target.setAttribute('aria-selected', 'true');
      target.removeAttribute('tabindex');
      this.dispatch('selected', {
        bubbles: true,
        cancelable: false,
        detail: {
          current: currentPanelId,
          previous: previousPanelId,
          tabs: this.element,
        },
        target,
      });
    });

    // Run transitions (potentially with timeout) for the panels
    // Adding & removing classes to trigger animations
    // Waiting for any transitions to complete before hiding the previous panel
    Promise.resolve(
      (async () => {
        const activeClasses = this.activeClasses;

        const previousPanel = panelTargets.find(
          ({ id }) => id === previousPanelId,
        );
        if (!previousPanel) return activeClasses;
        previousPanel.classList.remove(...activeClasses);
        await this.afterTransition(previousPanel);
        previousPanel.hidden = true;

        return activeClasses;
      })(),
    ).then(async (activeClasses) => {
      panel.hidden = false;
      panel.classList.add(...activeClasses);
      await this.afterTransition(panel);
    });

    this.syncLocation();

    if (!previousPanelId) return;

    this.dispatch('changed', {
      bubbles: true,
      cancelable: false,
      detail: {
        current: currentPanelId,
        previous: previousPanelId,
        tabs: this.element,
      },
      target: panel,
    });
  }

  /**
   * Handles the completion of a transition or animation on the given element.
   * If transitions are enabled using the action value, the Promise returned will
   * resolve when either the animation is finished or the transition timeout value is reached.
   * If transitions are not enabled (0 or negative value) a Promise like with an immediate `then`
   * callback is returned.
   */
  afterTransition(element: HTMLElement) {
    const transitionValue = this.transitionValue || 0;

    if (transitionValue <= 0) return immediatePromiseLike(element);

    return new Promise<HTMLElement>((resolve) => {
      let timer: number | undefined;
      const finish = (event: AnimationEvent | TransitionEvent | undefined) => {
        if (event && event.target !== element) return;
        window.clearTimeout(timer);
        element.removeEventListener('transitionend', finish);
        element.removeEventListener('animationend', finish);
        resolve(element);
      };
      element.addEventListener('animationend', finish, { once: true });
      element.addEventListener('transitionend', finish, { once: true });
      timer = window.setTimeout(finish, transitionValue);
    });
  }

  get locationPanelId() {
    if (!this.useLocationValue) return null;

    const locationHash = window.location.hash;

    if (!locationHash) return null;

    const anchorId = locationHash.slice(1);
    const element =
      document.getElementById(anchorId) || getElementByContentPath();

    if (!element) return null;

    return (
      this.panelTargets.find((panel) => panel.contains(element))?.id || null
    );
  }

  /**
   * Set the active panel based on a provided id either from the event if it's a history (PopStateEvent)
   * the target element's aria-controls, custom event details or action params.
   */
  select(
    event?:
      | (Event & { params?: { id?: string } })
      | CustomEvent<{ id?: string }>
      | PopStateEvent,
  ) {
    if (!event) return null;

    if ('state' in event && event.state) {
      const panelId = event.state[this.historyStateKey];
      if (panelId) {
        this.activePanelIdValue = panelId;
        this.tabs
          .filter((tab) => tab.getAttribute('aria-controls') === panelId)
          .forEach((tab) => tab.focus());

        return panelId;
      }
    }

    const { id } = {
      ...('params' in event && event.params),
      ...('detail' in event && event.detail),
    };

    if (id) {
      const panelId = id;
      this.activePanelIdValue = panelId;
      return panelId;
    }

    if (event.target instanceof HTMLElement) {
      const panelId = event.target.getAttribute('aria-controls');
      if (panelId) {
        this.activePanelIdValue = panelId;
        return panelId;
      }
    }

    return null;
  }

  /**
   * Set the first tab's panel to the active panel.
   */
  selectFirst(event?: Event) {
    const tab = this.tabs[0];
    const panelId = tab.getAttribute('aria-controls');
    this.activePanelIdValue = panelId;
    if (event) tab.focus();
    return panelId;
  }

  /**
   * Set the last tab's panel to the active panel.
   */
  selectLast(event?: Event) {
    const tabs = this.tabs;
    const tab = tabs[tabs.length - 1];
    const panelId = tab.getAttribute('aria-controls');
    this.activePanelIdValue = panelId;
    if (event) tab.focus();
    return panelId;
  }

  /**
   * Set the active panel based on the next tab in the DOM order.
   * If the current active panel is already the last tab, keep this panel active.
   */
  selectNext(event?: Event) {
    const activePanelIdValue = this.activePanelIdValue;
    const tabs = this.tabs;

    const currentIndex = tabs.findIndex(
      (tab) => tab.getAttribute('aria-controls') === activePanelIdValue,
    );

    const tab = tabs[(currentIndex + 1) % tabs.length];
    const panelId = tab.getAttribute('aria-controls');
    this.activePanelIdValue = panelId;

    if (event) tab.focus();

    return panelId;
  }

  /**
   * Set the active panel based on the previous tab in the DOM order.
   * If the current active panel is already the first tab, keep this panel active.
   */
  selectPrevious(event?: Event) {
    const activePanelIdValue = this.activePanelIdValue;
    const tabs = this.tabs;

    const currentIndex = tabs.findIndex(
      (tab) => tab.getAttribute('aria-controls') === activePanelIdValue,
    );

    const tab = tabs[(currentIndex - 1 + tabs.length) % tabs.length];
    const panelId = tab.getAttribute('aria-controls');

    this.activePanelIdValue = panelId;
    if (event) tab.focus();

    return panelId;
  }

  /**
   * If the initial panel is found, set it as the active panel,
   * if the value is already set (from the DOM value), trigger the value changed callback.
   *
   * If no initial panel is found, the first tab will be selected.
   *
   * @description
   * The initial active panel is based on:
   * 1. Location (URL) based if enabled & matching location found
   * 2. Existing value set in the HTML (can be overridden from the param)
   * 3. First tab with aria-selected='true'
   * 4. Fall back to selection of the first panel
   */
  setInitialPanel() {
    const initialActivePanelIdValue = this.activePanelIdValue;

    const initialPanelId =
      this.locationPanelId ||
      initialActivePanelIdValue ||
      this.triggerTargets
        .find((tab) => tab.getAttribute('aria-selected') === 'true')
        ?.getAttribute('aria-controls') ||
      this.selectFirst();

    if (initialPanelId && initialActivePanelIdValue === initialPanelId) {
      // ensure we manually trigger the value changed callback (so it runs after tabs are set up)
      this.activePanelIdValueChanged(initialPanelId, '');
    } else {
      this.activePanelIdValue = initialPanelId;
    }

    return initialPanelId;
  }

  /**
   * Update the URL (location) hash based on the active panel id,
   * only if configured to be syncing location.
   * If state is available, add a new history item to the stack.
   */
  syncLocation() {
    if (!this.useLocationValue) return null;

    const activePanelId = this.activePanelIdValue;
    const historyStateKey = this.historyStateKey;

    if (
      !window.history.state ||
      window.history.state[historyStateKey] !== activePanelId
    ) {
      const data = { [historyStateKey]: activePanelId };
      window.history.pushState(data, '', `#${activePanelId}`);

      return activePanelId;
    }

    return null;
  }

  /**
   * Validates and patches in missing aria-controls values if needed.
   * Returning only the triggers that are located within `tablist`.
   *
   * @description
   * Avoid calling this directly, unless needing to re-run validation
   * instead use the cached `this.tabs` or the full set of `this.toggleTargets`.
   */
  get validatedTabs() {
    const identifier = this.identifier;
    const tabList = this.element.querySelector('[role="tablist"]');

    if (!tabList) {
      throw new Error(
        "There must be an element with `role='tablist'` within the controller's scope.",
      );
    }

    const panels = this.panelTargets.map((panel) => {
      if (!(panel.getAttribute('role') === 'tabpanel')) {
        throw new Error(
          "Tab panel elements must have the `role='tabpanel'` attribute set",
          { cause: panel },
        );
      }
      return panel;
    });

    if (!panels.length) {
      throw new Error(
        `Tabs must be supplied with at least one panel target using 'data-${identifier}-target="panel"'.`,
      );
    }

    const validatedTabs = this.triggerTargets.filter((trigger) => {
      const idParamAttribute = `data-${identifier}-id-param`;

      const panelId =
        trigger.getAttribute('aria-controls') ||
        trigger.getAttribute('href')?.replace('#', '') ||
        trigger.getAttribute(idParamAttribute);

      const panel = panels.find(({ id }) => id === panelId);

      if (!panelId || !panel) {
        throw new Error(
          `Cannot find matching a matching panel for the trigger/tab in 'aria-controls', 'href' or '${idParamAttribute}'.`,
          { cause: trigger },
        );
      }

      trigger.setAttribute('aria-controls', panelId); // set if not already in HTML

      // check if the tab is a descendant of the tabList
      const isTab = tabList.contains(trigger);

      if (!isTab) return false;

      if (
        !(panel.getAttribute('aria-labelledby') || '')
          .split(' ')
          .includes(trigger.id)
      ) {
        throw new Error(
          'Panel targets must have a panels must be labelled by their tab.',
          { cause: panel },
        );
      }

      if (!(trigger.getAttribute('role') === 'tab')) {
        throw new Error('Tabs must use `role=tab`.', { cause: trigger });
      }

      return true;
    });

    if (!validatedTabs.length) {
      throw new Error(
        `Tabs must be supplied with at least one valid tab target using 'data-${identifier}-target="trigger"' within role="tablist".`,
      );
    }

    if (validatedTabs.length !== panels.length) {
      throw new Error(
        'Each tab panel must have a valid tab within the "role=tablist".',
      );
    }

    return validatedTabs;
  }

  // -- Target changed callbacks get set up during connect -- //

  panelTargetConnected() {}

  panelTargetDisconnected() {}

  triggerTargetConnected() {}

  triggerTargetDisconnected() {}
}
