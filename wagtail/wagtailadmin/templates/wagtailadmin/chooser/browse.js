function(modal) {
    $('a.navigate-pages, .link-types a', modal.body).click(function() {
        modal.loadUrl(this.href);
        return false;
    });

    {% include 'wagtailadmin/chooser/_search_behaviour.js' %}

    $('a.choose-page', modal.body).click(function() {
        var pageData = $(this).data();
        pageData.parentId = {{ parent_page.id }};
        modal.respond('pageChosen', $(this).data());
        modal.close();

        return false;
    });
}
