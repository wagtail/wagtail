(function(w, d) {
    "use strict";

    var l, f, t, frame_height;

    function callback(e) {
        var h;
        if (e.origin !== w.wagtail.userbar.origin) {return;};

        // Get the height from the passed data.
        try {
            h = Number(e.data.replace(/.*fh=(\d+)(?:&|$)/, '$1'));
            if (!isNaN(h) && h > 0 && h !== frame_height) {
                f.style.opacity = 1;
                f.style.height = h + "px";
            }
        } catch (e) {}
    }

    if (!w.wagtail) return;

    if (w.postMessage) {
        if (w.addEventListener) {
            w.addEventListener('message', callback, false);
        } else {
            w.attachEvent('onmessage', callback);
        }
    }

    l = d.createElement('link'); 
    l.rel = 'stylesheet';
    l.href = w.wagtail.static_root + 'scss/userbar_embed.css';

    f = d.createElement('iframe');
    f.id = 'wagtail-userbar'; 
    f.frameborder = '0'; 
    f.allowtransparency = 'true'; 
    f.scrolling = 'no';
    f.src = w.wagtail.userbar.src;

    // if postMessage is supported, hide iframe till it is loaded
    if (w.postMessage) {
        f.style.opacity = 0;
    }

    t = d.getElementsByTagName('title')[0]; 
    t.parentNode.insertBefore(l, t.nextSibling);
    d.body.appendChild(f);
}(window, document));
