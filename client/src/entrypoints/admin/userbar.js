// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

// This component implements a roving tab index for keyboard navigation
// Learn more about roving tabIndex: https://w3c.github.io/aria-practices/#kbd_roving_tabindex

import { Sa11y, Lang, LangEn, Sa11yCustomChecks } from 'sa11y';

// Overrides original Sa11y's methods
class CustomSa11y extends Sa11y {
  constructor(options) {
    super(options);

    // Re-implement Sa11y's updateBadge method to show only number of errors
    this.updateBadge = () => {
      const userbarTrigger = document.getElementById('wagtail-userbar-trigger');
      const notifBadge = document.getElementById('sa11y-notification-badge');
      const notifCount = document.getElementById('sa11y-notification-count');
      const notifText = document.getElementById('sa11y-notification-text');

      const errorsCount = this.errorCount;
      if (errorsCount === 0) {
        notifBadge.style.display = 'none';
      } else {
        notifBadge.style.display = 'flex';
        notifCount.innerText = `${errorsCount}`;
        notifText.innerText = Lang._('PANEL_ICON_TOTAL');
      }

      userbarTrigger.appendChild(notifBadge);
    };

    // Re-implement Sa11y's initialize method
    this.initialize = () => {
      // Added because otherwise Sa11y doesn't catch all errors
      const documentLoadingCheck = (callback) => {
        if (document.readyState === 'complete') {
          callback();
        } else {
          window.addEventListener('load', callback);
        }
      };

      this.globals();
      this.utilities();

      documentLoadingCheck(() => {
        this.buildSa11yUI();
        this.settingPanelToggles();
        this.customMainToggle();
        this.skipToIssueTooltip();
        this.detectPageChanges();

        // Pass Sa11y instance to custom checker
        if (options.customChecks && options.customChecks.setSa11y) {
          options.customChecks.setSa11y(this);
        }

        // Check page once page is done loading.
        document.getElementById('sa11y-toggle').disabled = false;
        if (
          this.store.getItem('sa11y-remember-panel') === 'Closed' ||
          !this.store.getItem('sa11y-remember-panel')
        ) {
          this.panelActive = true;
          this.checkAll();
        }
      });
    };
  }

  // Re-implement Sa11y's buildUI method to remove sa11y's trigger button. Rendering, and then removing a node didn't seem right to me
  buildSa11yUI = () => {
    const sa11ycontainer = document.createElement('div');
    sa11ycontainer.setAttribute('id', 'sa11y-container');
    sa11ycontainer.setAttribute('role', 'region');
    sa11ycontainer.setAttribute('lang', Lang._('LANG_CODE'));
    sa11ycontainer.setAttribute('aria-label', Lang._('CONTAINER_LABEL'));

    const loadContrastPreference =
      this.store.getItem('sa11y-remember-contrast') === 'On';
    const loadLabelsPreference =
      this.store.getItem('sa11y-remember-labels') === 'On';
    const loadChangeRequestPreference =
      this.store.getItem('sa11y-remember-links-advanced') === 'On';
    const loadReadabilityPreference =
      this.store.getItem('sa11y-remember-readability') === 'On';

    sa11ycontainer.innerHTML =
      `<div id="sa11y-notification-badge">
              <span id="sa11y-notification-count"></span>
              <span id="sa11y-notification-text" class="sa11y-visually-hidden"></span>
        </div>` +
      // Start of main container.
      '<div id="sa11y-panel">' +
      // Page Outline tab.
      `<div id="sa11y-outline-panel" role="tabpanel" aria-labelledby="sa11y-outline-header">
              <div id="sa11y-outline-header" class="sa11y-header-text">
                  <h2 tabindex="-1">${Lang._('PAGE_OUTLINE')}</h2>
              </div>
              <div id="sa11y-outline-content">
                  <ul id="sa11y-outline-list" tabindex="0" role="list" aria-label="${Lang._(
                    'PAGE_OUTLINE',
                  )}"></ul>
              </div>` +
      // Readability tab.
      `<div id="sa11y-readability-panel">
                  <div id="sa11y-readability-content">
                      <h2 class="sa11y-header-text-inline">${Lang._(
                        'LANG_READABILITY',
                      )}</h2>
                      <p id="sa11y-readability-info"></p>
                      <ul id="sa11y-readability-details"></ul>
                  </div>
              </div>
          </div>` + // End of Page Outline tab.
      // Settings tab.
      `<div id="sa11y-settings-panel" role="tabpanel" aria-labelledby="sa11y-settings-header">
              <div id="sa11y-settings-header" class="sa11y-header-text">
                  <h2 tabindex="-1">${Lang._('SETTINGS')}</h2>
              </div>
              <div id="sa11y-settings-content">
                  <ul id="sa11y-settings-options">
                      <li id="sa11y-contrast-li">
                          <label id="sa11y-check-contrast" for="sa11y-contrast-toggle">${Lang._(
                            'CONTRAST',
                          )}</label>
                          <button id="sa11y-contrast-toggle"
                          aria-labelledby="sa11y-check-contrast"
                          class="sa11y-settings-switch"
                          aria-pressed="${
                            loadContrastPreference ? 'true' : 'false'
                          }">${
        loadContrastPreference ? Lang._('ON') : Lang._('OFF')
      }</button></li>
                      <li id="sa11y-form-labels-li">
                          <label id="sa11y-check-labels" for="sa11y-labels-toggle">${Lang._(
                            'FORM_LABELS',
                          )}</label>
                          <button id="sa11y-labels-toggle" aria-labelledby="sa11y-check-labels" class="sa11y-settings-switch"
                          aria-pressed="${
                            loadLabelsPreference ? 'true' : 'false'
                          }">${
        loadLabelsPreference ? Lang._('ON') : Lang._('OFF')
      }</button>
                      </li>
                      <li id="sa11y-links-advanced-li">
                          <label id="check-changerequest" for="sa11y-links-advanced-toggle">${Lang._(
                            'LINKS_ADVANCED',
                          )} <span class="sa11y-badge">AAA</span></label>
                          <button id="sa11y-links-advanced-toggle" aria-labelledby="check-changerequest" class="sa11y-settings-switch"
                          aria-pressed="${
                            loadChangeRequestPreference ? 'true' : 'false'
                          }">${
        loadChangeRequestPreference ? Lang._('ON') : Lang._('OFF')
      }</button>
                      </li>
                      <li id="sa11y-readability-li">
                          <label id="check-readability" for="sa11y-readability-toggle">${Lang._(
                            'LANG_READABILITY',
                          )} <span class="sa11y-badge">AAA</span></label>
                          <button id="sa11y-readability-toggle" aria-labelledby="check-readability" class="sa11y-settings-switch"
                          aria-pressed="${
                            loadReadabilityPreference ? 'true' : 'false'
                          }">${
        loadReadabilityPreference ? Lang._('ON') : Lang._('OFF')
      }</button>
                      </li>
                      <li>
                          <label id="sa11y-dark-mode" for="sa11y-theme-toggle">${Lang._(
                            'DARK_MODE',
                          )}</label>
                          <button id="sa11y-theme-toggle" aria-labelledby="sa11y-dark-mode" class="sa11y-settings-switch"></button>
                      </li>
                  </ul>
              </div>
          </div>` +
      // Console warning messages.
      `<div id="sa11y-panel-alert">
              <div class="sa11y-header-text">
                  <button id="sa11y-close-alert" class="sa11y-close-btn" aria-label="${Lang._(
                    'ALERT_CLOSE',
                  )}" aria-describedby="sa11y-alert-heading sa11y-panel-alert-text"></button>
                  <h2 id="sa11y-alert-heading">${Lang._('ALERT_TEXT')}</h2>
              </div>
              <p id="sa11y-panel-alert-text"></p>
              <div id="sa11y-panel-alert-preview"></div>
          </div>` +
      // Main panel that conveys state of page.
      `<div id="sa11y-panel-content">
              <button id="sa11y-cycle-toggle" type="button" aria-label="${Lang._(
                'SHORTCUT_SCREEN_READER',
              )}">
                  <div class="sa11y-panel-icon"></div>
              </button>
              <div id="sa11y-panel-text"><h1 class="sa11y-visually-hidden">${Lang._(
                'PANEL_HEADING',
              )}</h1>
              <p id="sa11y-status" aria-live="polite"></p>
              </div>
          </div>` +
      // Show Outline & Show Settings button.
      `<div id="sa11y-panel-controls" role="tablist" aria-orientation="horizontal">
              <button type="button" role="tab" aria-expanded="false" id="sa11y-outline-toggle" aria-controls="sa11y-outline-panel">
                  ${Lang._('SHOW_OUTLINE')}
              </button>
              <button type="button" role="tab" aria-expanded="false" id="sa11y-settings-toggle" aria-controls="sa11y-settings-panel">
                  ${Lang._('SHOW_SETTINGS')}
              </button>
              <div style="width:40px;"></div>
          </div>` +
      // End of main container.
      '</div>';

    const userbar = document.querySelector('[data-wagtail-userbar]');
    userbar.append(sa11ycontainer);
  };

  // Re-implement Sa11y's mainToggle method triggering panel closing by clicking on the userbar icon
  customMainToggle() {
    this.mainToggle();
    const userbarTrigger = document.getElementById('wagtail-userbar-trigger');
    userbarTrigger.addEventListener('click', (e) => {
      if (this.store.getItem('sa11y-remember-panel') === 'Opened') {
        this.store.setItem('sa11y-remember-panel', 'Closed');
        this.resetAll();
        this.updateBadge();
        e.preventDefault();
      }
    });
  }
}

// Custom Sa11y initialize
const sa11y = new CustomSa11y({
  customChecks: new Sa11yCustomChecks(),
  // Use doNotRun to initialize Sa11y without UI render
  doNotRun: 'body',
  checkRoot: 'body',
  readabilityRoot: 'main',
  containerIgnore: '.wagtail-userbar-reset',
});

Lang.addI18n(LangEn.strings);
sa11y.initialize();

document.addEventListener('DOMContentLoaded', () => {
  const userbar = document.querySelector('[data-wagtail-userbar]');
  const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
  const list = userbar.querySelector('[role=menu]');
  const listItems = list.querySelectorAll('li');
  const isActiveClass = 'is-active';
  const sa11yToggle = document.getElementById('sa11y-toggle');

  // querySelector for all items that can be focused
  // tabIndex has been removed for roving tabindex compatibility
  // source: https://stackoverflow.com/questions/1599660/which-html-elements-can-receive-focus
  const focusableItemSelector = `a[href],
    button:not([disabled]),
    input:not([disabled])`;

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  trigger.addEventListener('click', toggleUserbar, false);

  // make sure userbar is hidden when Sa11y is open
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  sa11yToggle.addEventListener('click', hideUserbar, false);

  // make sure userbar is hidden when navigating back
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  window.addEventListener('pageshow', hideUserbar, false);

  // Handle keyboard events on the trigger
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  userbar.addEventListener('keydown', handleTriggerKeyDown);
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  list.addEventListener('focusout', handleFocusChange);

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  resetItemsTabIndex(); // On initialisation, all menu items should be disabled for roving tab index

  function showUserbar(shouldFocus) {
    userbar.classList.add(isActiveClass);
    trigger.setAttribute('aria-expanded', 'true');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener('click', sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.addEventListener('click', clickOutside, false);

    // Start handling keyboard input now that the userbar is open.
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    userbar.addEventListener('keydown', handleUserbarItemsKeyDown, false);

    // The userbar has role=menu which means that the first link should be focused on popup
    // For weird reasons shifting focus only works after some amount of delay
    // Which is why we are forced to use setTimeout
    if (shouldFocus) {
      // Find the first focusable element (if any) and focus it
      if (list.querySelector(focusableItemSelector)) {
        setTimeout(() => {
          // eslint-disable-next-line @typescript-eslint/no-use-before-define
          setFocusToFirstItem();
        }, 300); // Less than 300ms doesn't seem to work
      }
    }
  }

  function hideUserbar() {
    userbar.classList.remove(isActiveClass);
    trigger.setAttribute('aria-expanded', 'false');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener('click', sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.removeEventListener('click', clickOutside, false);

    // Cease handling keyboard input now that the userbar is closed.
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    userbar.removeEventListener('keydown', handleUserbarItemsKeyDown, false);
  }

  function toggleUserbar(e2) {
    e2.stopPropagation();
    if (userbar.classList.contains(isActiveClass)) {
      hideUserbar();
    } else {
      showUserbar(true);
    }
  }

  function isFocusOnItems() {
    return (
      document.activeElement &&
      !!document.activeElement.closest('.wagtail-userbar-items')
    );
  }

  /** Reset all focusable menu items to `tabIndex = -1` */
  function resetItemsTabIndex() {
    listItems.forEach((listItem) => {
      // eslint-disable-next-line no-param-reassign
      listItem.firstElementChild.tabIndex = -1;
    });
  }

  /** Focus element using a roving tab index */
  function focusElement(el) {
    resetItemsTabIndex();
    // eslint-disable-next-line no-param-reassign
    el.tabIndex = 0;
    setTimeout(() => {
      el.focus();
    }, 100); // Workaround, changing focus only works after a timeout
  }

  function setFocusToTrigger() {
    setTimeout(() => trigger.focus(), 300);
    resetItemsTabIndex();
  }

  function setFocusToFirstItem() {
    if (listItems.length > 0) {
      focusElement(listItems[0].firstElementChild);
    }
  }

  function setFocusToLastItem() {
    if (listItems.length > 0) {
      focusElement(listItems[listItems.length - 1].firstElementChild);
    }
  }

  function setFocusToNextItem() {
    listItems.forEach((element, idx) => {
      // Check which item is currently focused
      if (element.firstElementChild === document.activeElement) {
        if (idx + 1 < listItems.length) {
          focusElement(listItems[idx + 1].firstElementChild);
        } else {
          // Loop around
          setFocusToFirstItem();
        }
      }
    });
  }

  function setFocusToPreviousItem() {
    listItems.forEach((element, idx) => {
      // Check which item is currently focused
      if (element.firstElementChild === document.activeElement) {
        if (idx > 0) {
          focusElement(listItems[idx - 1].firstElementChild);
        } else {
          setFocusToLastItem();
        }
      }
    });
  }

  /**
    This handler is responsible for keyboard input when items inside the userbar are focused.
    It should only listen when the userbar is open.

    It is responsible for:
    - Shifting focus using the arrow / home / end keys.
    - Closing the menu when 'Escape' is pressed.
  */
  function handleUserbarItemsKeyDown(event) {
    // Only handle keyboard input if the userbar is open
    if (trigger.getAttribute('aria-expanded') === 'true') {
      if (event.key === 'Escape') {
        hideUserbar();
        setFocusToTrigger();
        return false;
      }

      // List items are in focus, move focus if needed
      if (isFocusOnItems()) {
        switch (event.key) {
          case 'ArrowDown':
            event.preventDefault();
            setFocusToNextItem();
            return false;
          case 'ArrowUp':
            event.preventDefault();
            setFocusToPreviousItem();
            return false;
          case 'Home':
            event.preventDefault();
            setFocusToFirstItem();
            return false;
          case 'End':
            event.preventDefault();
            setFocusToLastItem();
            return false;
          default:
            break;
        }
      }
    }
    return true;
  }

  function handleFocusChange(event) {
    // Is the focus is still in the menu? If so, don't to anything
    if (
      event.relatedTarget == null ||
      (event.relatedTarget &&
        event.relatedTarget.closest('.wagtail-userbar-items'))
    ) {
      return;
    }
    // List items not in focus - the menu should close
    resetItemsTabIndex();
    hideUserbar();
  }

  /**
    This handler is responsible for opening the userbar with the arrow keys
    if it's focused and not open yet. It should always be listening.
  */
  function handleTriggerKeyDown(event) {
    // Check if the userbar is focused (but not open yet) and should be opened by keyboard input
    if (
      trigger === document.activeElement &&
      trigger.getAttribute('aria-expanded') === 'false'
    ) {
      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          showUserbar(false);

          // Workaround for focus bug
          // Needs extra delay to account for the userbar open animation. Otherwise won't focus properly.
          setTimeout(() => setFocusToLastItem(), 300);
          break;
        case 'ArrowDown':
          event.preventDefault();
          showUserbar(false);

          // Workaround for focus bug
          // Needs extra delay to account for the userbar open animation. Otherwise won't focus properly.
          setTimeout(() => setFocusToFirstItem(), 300);
          break;
        default:
          break;
      }
    }
  }

  function sandboxClick(e2) {
    e2.stopPropagation();
  }

  function clickOutside() {
    hideUserbar();
  }
});
