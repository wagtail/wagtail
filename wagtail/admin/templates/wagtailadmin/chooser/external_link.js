function(modal) {
    $('p.link-types a', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });
}
