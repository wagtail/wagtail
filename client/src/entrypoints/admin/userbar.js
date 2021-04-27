// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

document.addEventListener('DOMContentLoaded', (e) => {
  const userbar = document.querySelector('[data-wagtail-userbar]');
  const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
  const list = userbar.querySelector('.wagtail-userbar-items');
  const listItems = list.querySelectorAll('li');
  const isActiveClass = 'is-active';
  const clickEvent = 'click';

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  trigger.addEventListener(clickEvent, toggleUserbar, false);

  // make sure userbar is hidden when navigating back
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  window.addEventListener('pageshow', hideUserbar, false);

  // Listen for keyboard events
  window.addEventListener('keydown', handleKeyDown);

  function isFocusOnItems() {
    let isFocused = false;
    list.querySelectorAll('a').forEach((element) => {
      if (element === document.activeElement) {
        isFocused = true;
      }
    });
    return isFocused;
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
      }, 100);  // Workaround for focus bug
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
          }
        }, 100);  // Workaround for focus bug
      }
    });
  }

  function handleKeyDown(event) {
    // Only handle keyboard input if the userbar is open
    if(userbar.classList.contains(isActiveClass)) {
      if (event.key === 'Escape') {
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        hideUserbar();
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
    }
    // Check if the userbar is focused (but not open yet) and should be opened by keyboard input
    else {
      if(trigger === document.activeElement) {
        switch (event.key) {
          case "ArrowUp":
            event.preventDefault();
            showUserbar(false);
            setTimeout(() => setFocusToFirstItem(), 300); // Workaround for focus bug
            break;
          case "ArrowDown":
            event.preventDefault();
            showUserbar(false);
            setTimeout(() => setFocusToLastItem(), 300); // Workaround for focus bug
            break;
          default:
            break;
        }
      }
    }
  }

  function showUserbar(shouldFocus) {
    userbar.classList.add(isActiveClass);
    trigger.setAttribute('aria-expanded', 'true');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener(clickEvent, sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.addEventListener(clickEvent, clickOutside, false);

    // The userbar has role=menu which means that the first link should be focused on popup
    // For weird reasons shifting focus only works after some amount of delay
    // Which is why we are forced to use setTimeout
    if(shouldFocus) {
      setTimeout(() => {
        list.querySelector('a').focus();
      }, 300); // Less than 300ms doesn't seem to work
    }
  }

  function hideUserbar() {
    userbar.classList.remove(isActiveClass);
    trigger.setAttribute('aria-expanded', 'false');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener(clickEvent, sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.removeEventListener(clickEvent, clickOutside, false);
  }

  function toggleUserbar(e2) {
    e2.stopPropagation();
    if (userbar.classList.contains(isActiveClass)) {
      hideUserbar();
    } else {
      showUserbar(true);
    }
  }

  function sandboxClick(e2) {
    e2.stopPropagation();
  }

  function clickOutside() {
    hideUserbar();
  }
});
