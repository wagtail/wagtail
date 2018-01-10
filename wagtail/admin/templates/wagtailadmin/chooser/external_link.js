function(modal) {
    $('p.link-types a', modal.body).on('click', function() {
        modal.loadUrl(this.href);
        return false;
    });

    $('form', modal.body).on('submit', function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });
}
