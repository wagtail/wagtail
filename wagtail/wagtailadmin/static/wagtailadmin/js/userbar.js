'use strict';

document.addEventListener('DOMContentLoaded', function() {
    var body = document.querySelectorAll('body')[0];
    var nav = document.querySelectorAll('nav')[0];
    var className = 'ready';
    var hasPostMessage = window.postMessage;

    if (hasPostMessage) {
        parent.postMessage('fh=' + nav.offsetHeight, '*');
    }

    if (body.classList) {
        body.classList.add(className);
    } else {
        body.className += ' ' + className;
    }
});
