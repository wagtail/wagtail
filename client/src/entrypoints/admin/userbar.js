// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

document.addEventListener('DOMContentLoaded', () => {
  const userbar = document.querySelector('[data-wagtail-userbar]');
  const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
  const list = userbar.querySelector('[role=menu]');
  const listItems = list.querySelectorAll('li');
  const isActiveClass = 'is-active';

  // querySelector for all items that can be focused.
  // source: https://stackoverflow.com/questions/1599660/which-html-elements-can-receive-focus
  const focusableItemSelector = `a[href]:not([tabindex='-1']),
    button:not([disabled]):not([tabindex='-1']),
    input:not([disabled]):not([tabindex='-1']),
    [tabindex]:not([tabindex='-1'])`;

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  trigger.addEventListener('click', toggleUserbar, false);

  // make sure userbar is hidden when navigating back
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  window.addEventListener('pageshow', hideUserbar, false);

  // Handle keyboard events on the trigger
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  userbar.addEventListener('keydown', handleTriggerKeyDown);


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

  function setFocusToTrigger() {
    setTimeout(() => trigger.focus(), 300);
  }

  function isFocusOnItems() {
    return document.activeElement && !!document.activeElement.closest('.wagtail-userbar-items');
  }

  function setFocusToFirstItem() {
    if (listItems.length > 0) {
      setTimeout(() => {
        listItems[0].firstElementChild.focus();
      }, 100); // Workaround for focus bug
    }
  }

  function setFocusToLastItem() {
    if (listItems.length > 0) {
      setTimeout(() => {
        listItems[listItems.length - 1].firstElementChild.focus();
      }, 100); // Workaround for focus bug
    }
  }

  function setFocusToNextItem() {
    listItems.forEach((element, idx) => {
      // Check which item is currently focused
      if (element.firstElementChild === document.activeElement) {
        setTimeout(() => {
          if (idx + 1 < listItems.length) {
            // Focus the next item
            listItems[idx + 1].firstElementChild.focus();
          } else {
            setFocusToFirstItem();
          }
        }, 100); // Workaround for focus bug
      }
    });
  }

  function setFocusToPreviousItem() {
    // Check which item is currently focused
    listItems.forEach((element, idx) => {
      if (element.firstElementChild === document.activeElement) {
        setTimeout(() => {
          if (idx > 0) {
            // Focus the previous item
            listItems[idx - 1].firstElementChild.focus();
          } else {
            setFocusToLastItem();
          }
        }, 100); // Workaround for focus bug
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
        return;
      }

      if (isFocusOnItems()) {
        switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusToNextItem();
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusToPreviousItem();
          break;
        case 'Home':
          event.preventDefault();
          setFocusToFirstItem();
          break;
        case 'End':
          event.preventDefault();
          setFocusToLastItem();
          break;
        default:
          break;
        }
      }
      return;
    }
  }

  /**
    This handler is responsible for opening the userbar with the arrow keys
    if it's focused and not open yet. It should always be listening.
  */
  function handleTriggerKeyDown(event) {
    // Check if the userbar is focused (but not open yet) and should be opened by keyboard input
    if (trigger === document.activeElement && trigger.getAttribute('aria-expanded') === 'false') {
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
