function(modal) {
    $('form', modal.body).submit(function() {
        modal.postForm(this.action, $(this).serialize());
        return false;
    });
}
