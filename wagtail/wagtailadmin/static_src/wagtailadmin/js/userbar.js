'use strict';

document.addEventListener('DOMContentLoaded', function() {
    var trigger = document.querySelectorAll('[data-wagtail-userbar-trigger]')[0];
    var userbar = document.querySelectorAll('[data-wagtail-userbar]')[0];
    var className = 'is-active';

    if ('ontouchstart' in window) {
        userbar.classList.add("touch");
    } else {
        userbar.classList.add("no-touch");
    }

    trigger.addEventListener("mouseenter", showUserbar, false);
    userbar.addEventListener("mouseleave", hideUserbar, false);

    trigger.addEventListener("touchstart", toggleUserbar, false);

    // make sure userbar is hidden when navigating back
    window.addEventListener('pageshow', hideUserbar, false);

    function showUserbar() {
        userbar.classList.add(className);
    }

    function hideUserbar() {
        userbar.classList.remove(className);
    }

    function toggleUserbar() {
        userbar.classList.toggle(className);
    }
});
