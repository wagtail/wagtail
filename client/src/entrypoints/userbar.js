// This entrypoint is not bundled with any polyfills to keep it as light as possible
// Please stick to old JS APIs and avoid importing anything that might require a vendored module
// More background can be found in webpack.config.js

document.addEventListener('DOMContentLoaded', (e) => {
  const userbar = document.querySelector('[data-wagtail-userbar]');
  const trigger = userbar.querySelector('[data-wagtail-userbar-trigger]');
  const list = userbar.querySelector('.wagtail-userbar-items');
  const className = 'is-active';
  const hasTouch = 'ontouchstart' in window;
  const clickEvent = 'click';

  if (hasTouch) {
    userbar.classList.add('touch');

    // Bind to touchend event, preventDefault to prevent DELAY and CLICK
    // in accordance with: https://hacks.mozilla.org/2013/04/detecting-touch-its-the-why-not-the-how/
    trigger.addEventListener('touchend', (e2) => {
      e.preventDefault();
      // eslint-disable-next-line no-use-before-define
      toggleUserbar(e2);
    });
  } else {
    userbar.classList.add('no-touch');
  }

  // eslint-disable-next-line no-use-before-define
  trigger.addEventListener(clickEvent, toggleUserbar, false);

  // make sure userbar is hidden when navigating back
  // eslint-disable-next-line no-use-before-define
  window.addEventListener('pageshow', hideUserbar, false);

  function showUserbar() {
    userbar.classList.add(className);
    // eslint-disable-next-line no-use-before-define
    list.addEventListener(clickEvent, sandboxClick, false);
    // eslint-disable-next-line no-use-before-define
    window.addEventListener(clickEvent, clickOutside, false);
  }

  function hideUserbar() {
    userbar.classList.remove(className);
    // eslint-disable-next-line no-use-before-define
    list.addEventListener(clickEvent, sandboxClick, false);
    // eslint-disable-next-line no-use-before-define
    window.removeEventListener(clickEvent, clickOutside, false);
  }

  function toggleUserbar(e2) {
    e2.stopPropagation();
    if (userbar.classList.contains(className)) {
      hideUserbar();
    } else {
      showUserbar();
    }
  }

  function sandboxClick(e2) {
    e2.stopPropagation();
  }

  function clickOutside() {
    hideUserbar();
  }
});
