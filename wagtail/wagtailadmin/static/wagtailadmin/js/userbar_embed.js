(function(w,d){
    var l, f, h, frame_height;

    if(!w.wagtail) return;

    if(w.postMessage){
        function callback(e){
            // Get the height from the passed data.
            var h = Number(e.data.replace( /.*fh=(\d+)(?:&|$)/, '$1' ) );
            if (!isNaN( h ) && h > 0 && h !== frame_height) {
                f.style.height = h + "px";
            }
        }

        if (w.addEventListener) {
            w.addEventListener('message', callback, false);
        } else {
            w.attachEvent('onmessage', callback );
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
    f.src = w.wagtail.userbar_src;

    t = d.getElementsByTagName('title')[0]; 
    t.parentNode.insertBefore(l, t.nextSibling);
    d.body.appendChild(f); 
}(window,document));