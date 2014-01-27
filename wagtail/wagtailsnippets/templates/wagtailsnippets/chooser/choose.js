function(modal) {
    $('a.snippet-choice', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });
}