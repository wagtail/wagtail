function(modal) {
    $('.link-types a', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    {% include 'wagtailadmin/chooser/_search_behaviour.js' %}
    ajaxifySearchResults();
}
