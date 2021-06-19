// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

document.addEventListener('DOMContentLoaded', () => {
  const userbar = document.querySelector('[data-wagtail-userbar]');
  const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
  const list = userbar.querySelector('[role=menu]');
  const listItems = list.querySelectorAll('li');
  const isActiveClass = 'is-active';

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  trigger.addEventListener('click', toggleUserbar, false);

  // make sure userbar is hidden when navigating back
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  window.addEventListener('pageshow', hideUserbar, false);

  // Listen for keyboard events
  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  window.addEventListener('keydown', handleKeyDown);


  function showUserbar(shouldFocus) {
    userbar.classList.add(isActiveClass);
    trigger.setAttribute('aria-expanded', 'true');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener('click', sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.addEventListener('click', clickOutside, false);

    // The userbar has role=menu which means that the first link should be focused on popup
    // For weird reasons shifting focus only works after some amount of delay
    // Which is why we are forced to use setTimeout
    if (shouldFocus) {
      setTimeout(() => {
        list.querySelector('a').focus();
      }, 300); // Less than 300ms doesn't seem to work
    }
  }

  function hideUserbar() {
    userbar.classList.remove(isActiveClass);
    trigger.setAttribute('aria-expanded', 'false');
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    list.addEventListener('click', sandboxClick, false);
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    window.removeEventListener('click', clickOutside, false);
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

  function handleKeyDown(event) {
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
    // Check if the userbar is focused (but not open yet) and should be opened by keyboard input
    if (trigger === document.activeElement) {
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
