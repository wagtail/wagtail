import axe from 'axe-core';

import A11yDialog from 'a11y-dialog';
import { Application } from '@hotwired/stimulus';
import {
  getAxeConfiguration,
  getA11yReport,
  renderA11yResults,
} from './a11y-result';
import { wagtailPreviewPlugin } from './previewPlugin';
import { contentMetricsPluginInstance } from './contentMetrics';
import { DialogController } from '../controllers/DialogController';
import { TeleportController } from '../controllers/TeleportController';

/*
This entrypoint is not bundled with any polyfills to keep it as light as possible
Please stick to old JS APIs and avoid importing anything that might require a vendored module
More background can be found in webpack.config.js

This component implements a roving tab index for keyboard navigation
Learn more about roving tabIndex: https://w3c.github.io/aria-practices/#kbd_roving_tabindex
*/

export class Userbar extends HTMLElement {
  declare trigger: HTMLElement;

  connectedCallback() {
    const template = document.querySelector<HTMLTemplateElement>(
      '#wagtail-userbar-template',
    );
    if (!template) return;
    const shadowRoot = this.attachShadow({
      mode: 'open',
    });
    shadowRoot.appendChild(
      (template.content.firstElementChild as HTMLElement).cloneNode(true),
    );
    // Removes the template from html after it's being used
    template.remove();

    const userbar = shadowRoot.querySelector<HTMLDivElement>(
      '[data-wagtail-userbar]',
    );
    const trigger = userbar?.querySelector<HTMLElement>(
      '[data-wagtail-userbar-trigger]',
    );
    const list = userbar?.querySelector<HTMLUListElement>('[role=menu]');

    if (!userbar || !trigger || !list) {
      return;
    }

    const listItems = list.querySelectorAll('li');
    const isActiveClass = 'w-userbar--active';

    this.trigger = trigger;

    // Avoid Web Component FOUC while stylesheets are loading.
    userbar.style.display = 'none';

    /*
    querySelector for all items that can be focused
    tabIndex has been removed for roving tabindex compatibility
    source: https://stackoverflow.com/questions/1599660/which-html-elements-can-receive-focus
    */
    const focusableItemSelector = `a[href],
    button:not([disabled]),
    input:not([disabled])`;

    const showUserbar = (shouldFocus: boolean) => {
      userbar.classList.add(isActiveClass);
      trigger.setAttribute('aria-expanded', 'true');
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      list.addEventListener('click', sandboxClick, false);
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      window.addEventListener('click', clickOutside, false);

      // Start handling keyboard input now that the userbar is open.
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      userbar.addEventListener('keydown', handleUserbarItemsKeyDown, false);

      /*
      The userbar has role=menu which means that the first link should be focused on popup
      For weird reasons shifting focus only works after some amount of delay
      Which is why we are forced to use setTimeout
      */
      if (shouldFocus) {
        // Find the first focusable element (if any) and focus it
        if (list.querySelector(focusableItemSelector)) {
          setTimeout(() => {
            // eslint-disable-next-line @typescript-eslint/no-use-before-define
            setFocusToFirstItem();
          }, 300); // Less than 300ms doesn't seem to work
        }
      }
    };

    const hideUserbar = () => {
      userbar.classList.remove(isActiveClass);
      trigger.setAttribute('aria-expanded', 'false');
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      list.addEventListener('click', sandboxClick, false);
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      window.removeEventListener('click', clickOutside, false);

      // Cease handling keyboard input now that the userbar is closed.
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      userbar.removeEventListener('keydown', handleUserbarItemsKeyDown, false);
    };

    const toggleUserbar = (event: MouseEvent) => {
      event.stopPropagation();
      if (userbar.classList.contains(isActiveClass)) {
        hideUserbar();
      } else {
        showUserbar(true);
      }
    };

    const isFocusOnItems = () =>
      shadowRoot.activeElement &&
      shadowRoot.activeElement.closest('.w-userbar-nav');

    // Reset all focusable menu items to `tabIndex = -1`
    const resetItemsTabIndex = () => {
      listItems.forEach((listItem) => {
        // eslint-disable-next-line no-param-reassign
        (listItem.firstElementChild as HTMLElement).tabIndex = -1;
      });
    };

    // Focus element using a roving tab index
    const focusElement = (el: HTMLElement) => {
      resetItemsTabIndex();
      // eslint-disable-next-line no-param-reassign
      el.tabIndex = 0;
      setTimeout(() => {
        el.focus();
      }, 100); // Workaround, changing focus only works after a timeout
    };

    const setFocusToTrigger = () => {
      if (!trigger) return;
      setTimeout(() => trigger.focus(), 300);
      resetItemsTabIndex();
    };

    const setFocusToFirstItem = () => {
      if (listItems.length > 0) {
        focusElement(listItems[0].firstElementChild as HTMLElement);
      }
    };

    const setFocusToLastItem = () => {
      if (listItems.length > 0) {
        focusElement(
          listItems[listItems.length - 1].firstElementChild as HTMLElement,
        );
      }
    };

    const setFocusToNextItem = () => {
      listItems.forEach((element, idx) => {
        // Check which item is currently focused
        if (element.firstElementChild === shadowRoot.activeElement) {
          if (idx + 1 < listItems.length) {
            focusElement(listItems[idx + 1].firstElementChild as HTMLElement);
          } else {
            // Loop around
            setFocusToFirstItem();
          }
        }
      });
    };

    const setFocusToPreviousItem = () => {
      listItems.forEach((element, idx) => {
        // Check which item is currently focused
        if (element.firstElementChild === shadowRoot.activeElement) {
          if (idx > 0) {
            focusElement(listItems[idx - 1].firstElementChild as HTMLElement);
          } else {
            setFocusToLastItem();
          }
        }
      });
    };

    /*
    This handler is responsible for keyboard input when items inside the userbar are focused.
    It should only listen when the userbar is open.

    It is responsible for:
    - Shifting focus using the arrow / home / end keys.
    - Closing the menu when 'Escape' is pressed.
    */
    const handleUserbarItemsKeyDown = (event: KeyboardEvent) => {
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
    };

    const handleFocusChange = (event: FocusEvent) => {
      // Is the focus is still in the menu? If so, don't to anything
      if (
        !event.relatedTarget ||
        (event.relatedTarget as HTMLElement).closest('.w-userbar-nav')
      ) {
        return;
      }
      // List items not in focus - the menu should close
      resetItemsTabIndex();
      hideUserbar();
    };

    /*
    This handler is responsible for opening the userbar with the arrow keys
    if it's focused and not open yet. It should always be listening.
    */
    const handleTriggerKeyDown = (event: KeyboardEvent) => {
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
    };

    const sandboxClick = (event: MouseEvent) => {
      event.stopPropagation();
    };

    const clickOutside = () => {
      hideUserbar();
    };

    trigger.addEventListener('click', toggleUserbar, false);

    // Make sure userbar is hidden when navigating back
    window.addEventListener('pageshow', hideUserbar, false);

    // Handle keyboard events on the trigger
    userbar.addEventListener('keydown', handleTriggerKeyDown);
    list.addEventListener('focusout', handleFocusChange);

    // On initialisation, all menu items should be disabled for roving tab index
    resetItemsTabIndex();

    document.addEventListener('DOMContentLoaded', async () => {
      await this.initialiseAxe();
    });
  }

  /*
  Integrating Axe accessibility checker to improve ATAG compliance, adapted for content authors to identify and fix accessibility issues.
  Scans loaded page for errors with 3 initial rules ('empty-heading', 'p-as-heading', 'heading-order') and outputs the results in GUI.
  See documentation: https://github.com/dequelabs/axe-core/tree/develop/doc
  */

  // Initialise Axe
  async initialiseAxe() {
    // Collect content data from the live preview via Axe plugin for content metrics calculation
    axe.registerPlugin(wagtailPreviewPlugin);
    axe.plugins.wagtailPreview.add(contentMetricsPluginInstance);

    const accessibilityTrigger = this.shadowRoot?.getElementById(
      'accessibility-trigger',
    );
    const config = getAxeConfiguration(this.shadowRoot);
    if (!this.shadowRoot || !accessibilityTrigger || !config) return;

    const { results, a11yErrorsNumber } = await getA11yReport(config);

    if (results.violations.length) {
      const a11yErrorBadge = document.createElement('span');
      a11yErrorBadge.textContent = String(a11yErrorsNumber);
      a11yErrorBadge.classList.add('w-userbar-axe-count');
      this.trigger.appendChild(a11yErrorBadge);
    }

    const stimulus = Application.start(
      this.shadowRoot.firstElementChild as Element,
    );

    stimulus.register('w-dialog', DialogController);
    stimulus.register('w-teleport', TeleportController);

    const modalReady = new Promise<{ body: HTMLElement; dialog: A11yDialog }>(
      (resolve) => {
        this.shadowRoot?.addEventListener(
          'w-dialog:ready',
          (({
            detail,
          }: CustomEvent<{ body: HTMLElement; dialog: A11yDialog }>) => {
            const { body, dialog } = detail;
            resolve({ body, dialog });
          }) as EventListener,
          { once: true, passive: true },
        );
      },
    );

    const { body: modalBody, dialog: modal } = await modalReady;

    // Disable TS linter check for legacy code in 3rd party `A11yDialog` element
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const accessibilityResultsBox = this.shadowRoot.querySelector(
      '#accessibility-results',
    );

    const a11yRowTemplate = this.shadowRoot.querySelector<HTMLTemplateElement>(
      '#w-a11y-result-row-template',
    );
    const a11yOutlineTemplate =
      this.shadowRoot.querySelector<HTMLTemplateElement>(
        '#w-a11y-result-outline-template',
      );

    if (!accessibilityResultsBox || !a11yRowTemplate || !a11yOutlineTemplate) {
      return;
    }

    const innerErrorBadges = this.shadowRoot.querySelectorAll<HTMLSpanElement>(
      '[data-a11y-result-count]',
    );
    innerErrorBadges.forEach((badge) => {
      // eslint-disable-next-line no-param-reassign
      badge.textContent = String(a11yErrorsNumber) || '0';
      badge.classList.toggle('has-errors', results.violations.length > 0);
    });

    const onClickSelector = (selectorName: string) => {
      const inaccessibleElement =
        document.querySelector<HTMLElement>(selectorName);
      const a11yOutlineContainer = this.shadowRoot?.querySelector<HTMLElement>(
        '[data-a11y-result-outline-container]',
      );
      if (a11yOutlineContainer?.firstElementChild) {
        a11yOutlineContainer.removeChild(
          a11yOutlineContainer.firstElementChild,
        );
      }
      a11yOutlineContainer?.appendChild(
        a11yOutlineTemplate.content.cloneNode(true),
      );
      const currentA11yOutline = this.shadowRoot?.querySelector<HTMLElement>(
        '[data-a11y-result-outline]',
      );
      if (
        !this.shadowRoot ||
        !inaccessibleElement ||
        !currentA11yOutline ||
        !a11yOutlineContainer
      )
        return;

      const styleA11yOutline = () => {
        const rect = inaccessibleElement.getBoundingClientRect();
        currentA11yOutline.style.cssText = `
        top: ${
          rect.height < 5
            ? `${rect.top + window.scrollY - 2.5}px`
            : `${rect.top + window.scrollY}px`
        };
        left: ${
          rect.width < 5
            ? `${rect.left + window.scrollX - 2.5}px`
            : `${rect.left + window.scrollX}px`
        };
        width: ${Math.max(rect.width, 5)}px;
        height: ${Math.max(rect.height, 5)}px;
        position: absolute;
        z-index: 129;
        outline: 1px solid #CD4444;
        box-shadow: 0px 0px 12px 1px #FF0000;
        pointer-events: none;
        `;
      };

      styleA11yOutline();

      window.addEventListener('resize', styleA11yOutline);

      inaccessibleElement.style.scrollMargin = '6.25rem';
      inaccessibleElement.scrollIntoView();
      inaccessibleElement.focus();

      accessibilityResultsBox.addEventListener('hide', () => {
        currentA11yOutline.style.cssText = '';

        window.removeEventListener('resize', styleA11yOutline);
      });
    };

    const toggleAxeResults = () => {
      if (accessibilityResultsBox.getAttribute('aria-hidden') === 'true') {
        modal.show();

        renderA11yResults(
          modalBody,
          results,
          config,
          a11yRowTemplate,
          onClickSelector,
        );
      } else {
        modal.hide();
      }
    };

    accessibilityTrigger.addEventListener('click', toggleAxeResults);
  }
}
