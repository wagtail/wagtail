function(modal) {
    $('p.link-types a', modal.body).click(function() {
        modal.loadUrl(this.href, buildUrlParams());
        return false;
    });

    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });

    function buildUrlParams() {
        return $('form input:visible', modal.body).serialize().replace('url', 'link_url');
    }
}
