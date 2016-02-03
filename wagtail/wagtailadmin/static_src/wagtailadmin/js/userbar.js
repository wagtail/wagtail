'use strict';

document.addEventListener('DOMContentLoaded', function() {
    var userbar = document.querySelectorAll('[data-wagtail-userbar]')[0];
    var className = 'is-active';

    userbar.addEventListener("mouseenter", showUserbar, false);
    userbar.addEventListener("mouseleave", hideUserbar, false);

    function showUserbar() {
        userbar.classList.add(className);
    }

    function hideUserbar() {
        userbar.classList.remove(className);
    }
});

