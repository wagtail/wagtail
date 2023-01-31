import axe from 'axe-core';

import { dialog } from '../../includes/dialog';

// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

// This component implements a roving tab index for keyboard navigation
// Learn more about roving tabIndex: https://w3c.github.io/aria-practices/#kbd_roving_tabindex

class Userbar extends HTMLElement {
  connectedCallback() {
    const template = document.getElementById('wagtail-userbar-template');
    const shadowRoot = this.attachShadow({
      mode: 'open',
    });
    shadowRoot.appendChild(template.content.cloneNode(true));
    // Removes the template from html after it's being used
    template.remove();

    const userbar = shadowRoot.querySelector('[data-wagtail-userbar]');
    const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
    this.trigger = trigger;
    const list = userbar.querySelector('[role=menu]');
    const listItems = list.querySelectorAll('li');
    const isActiveClass = 'is-active';

    // Avoid Web Component FOUC while stylesheets are loading.
    userbar.style.display = 'none';

    // querySelector for all items that can be focused
    // tabIndex has been removed for roving tabindex compatibility
    // source: https://stackoverflow.com/questions/1599660/which-html-elements-can-receive-focus
    const focusableItemSelector = `a[href],
    button:not([disabled]),
    input:not([disabled])`;

    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    trigger.addEventListener('click', toggleUserbar, false);

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
        shadowRoot.activeElement &&
        !!shadowRoot.activeElement.closest('.w-userbar-nav')
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
        if (element.firstElementChild === shadowRoot.activeElement) {
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
        if (element.firstElementChild === shadowRoot.activeElement) {
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
        (event.relatedTarget && event.relatedTarget.closest('.w-userbar-nav'))
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

    document.addEventListener('DOMContentLoaded', async () => {
      await this.initialiseAxe();
    });
  }

  // Integrating Axe accessibility checker to improve ATAG compliance, adapted for content authors to identify and fix accessibility issues.
  // Scans loaded page for errors with 3 initial rules ('empty-heading', 'p-as-heading', 'heading-order') and outputs the results in GUI.
  // See documentation: https://github.com/dequelabs/axe-core/tree/develop/doc
  getAxeConfiguration() {
    const script = this.shadowRoot.getElementById(
      'accessibility-axe-configuration',
    );
    try {
      return JSON.parse(script?.textContent);
    } catch (err) {
      /* eslint-disable no-console */
      console.error('Error loading Axe config');
      console.error(err);
    }

    // Skip initialization of Axe if config fails to load
    return null;
  }

  // Initialise axe accessibility checker
  async initialiseAxe() {
    const accessibilityTrigger = this.shadowRoot.getElementById(
      'accessibility-trigger',
    );

    if (!accessibilityTrigger) {
      return;
    }

    const config = this.getAxeConfiguration();

    if (!config) {
      return;
    }

    // Initialise Axe based on the configurable context (whole page body by default) and options ('empty-heading', 'p-as-heading' and 'heading-order' rules by default)
    const results = await axe.run(config.context, config.options);

    const a11yErrorsNumber = results.violations.reduce(
      (sum, violation) => sum + violation.nodes.length,
      0,
    );

    if (results.violations.length) {
      const a11yErrorBadge = document.createElement('span');
      a11yErrorBadge.textContent = a11yErrorsNumber;
      a11yErrorBadge.classList.add('w-userbar-axe-count');
      this.trigger.appendChild(a11yErrorBadge);
    }

    const dialogTemplates = this.shadowRoot.querySelectorAll(
      '[data-wagtail-dialog]',
    );
    const dialogs = dialog(dialogTemplates, this.shadowRoot);

    if (!dialogs.length) {
      return;
    }
    const modal = dialogs[0];
    const modalBody = modal.$el.querySelector('[data-dialog-body]');
    const accessibilityResultsBox = this.shadowRoot.querySelector(
      '#accessibility-results',
    );
    const a11yRowTemplate = this.shadowRoot.querySelector(
      '#w-a11y-result-row-template',
    );
    const a11ySelectorTemplate = this.shadowRoot.querySelector(
      '#w-a11y-result-selector-template',
    );

    const innerErrorBadges = this.shadowRoot.querySelectorAll(
      '[data-a11y-result-count]',
    );
    innerErrorBadges.forEach((badge) => {
      // eslint-disable-next-line no-param-reassign
      badge.textContent = a11yErrorsNumber || '0';
      if (results.violations.length) {
        badge.classList.add('has-errors');
      } else {
        badge.classList.remove('has-errors');
      }
    });

    const showAxeResults = () => {
      modal.show();
      // Reset modal contents to support multiple runs of Axe checks in the preview panel
      modalBody.innerHTML = '';

      if (results.violations.length) {
        results.violations.forEach((violation, violationIndex) => {
          modalBody.appendChild(a11yRowTemplate.content.cloneNode(true));
          const currentA11yRow = modalBody.querySelectorAll(
            '[data-a11y-result-row]',
          )[violationIndex];

          const a11yErrorName = currentA11yRow.querySelector(
            '[data-a11y-result-name]',
          );
          a11yErrorName.id = `w-a11y-result__name-${violationIndex}`;
          // Display custom error messages for rules supported by Wagtail out of the box, fallback to default error message from Axe
          a11yErrorName.textContent =
            config.messages[violation.id] || violation.help;
          const a11yErrorCount = currentA11yRow.querySelector(
            '[data-a11y-result-count]',
          );
          a11yErrorCount.textContent = violation.nodes.length;

          const a11yErrorContainer = currentA11yRow.querySelector(
            '[data-a11y-result-container]',
          );

          violation.nodes.forEach((node, nodeIndex) => {
            a11yErrorContainer.appendChild(
              a11ySelectorTemplate.content.cloneNode(true),
            );
            const currentA11ySelector = a11yErrorContainer.querySelectorAll(
              '[data-a11y-result-selector]',
            )[nodeIndex];

            currentA11ySelector.setAttribute(
              'aria-describedby',
              a11yErrorName.id,
            );
            const currentA11ySelectorText = currentA11ySelector.querySelector(
              '[data-a11y-result-selector-text]',
            );
            const selectorName = node.target[0];
            // Remove unnecessary details before displaying selectors to the user
            currentA11ySelectorText.textContent = selectorName.replace(
              /\[data-block-key="\w{5}"\]/,
              '',
            );
            currentA11ySelector.addEventListener('click', () => {
              const inaccessibleElement = document.querySelector(selectorName);
              inaccessibleElement.style.scrollMargin = '6.25rem';
              inaccessibleElement.scrollIntoView({
                behavior: 'smooth',
              });
              inaccessibleElement.focus();
            });
          });
        });
      }
    };

    const toggleAxeResults = () => {
      if (accessibilityResultsBox.getAttribute('aria-hidden') === 'true') {
        showAxeResults();
      } else {
        modal.hide();
      }
    };

    accessibilityTrigger.addEventListener('click', toggleAxeResults);
  }
}

customElements.define('wagtail-userbar', Userbar);
