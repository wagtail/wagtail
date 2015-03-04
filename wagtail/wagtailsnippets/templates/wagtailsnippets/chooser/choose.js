function(modal) {

    var listingUrl = $('#snippet-chooser-list', modal.body).data('url');

    function ajaxifyLinks (context) {
        $('a.snippet-choice', modal.body).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    function setPage(page) {

        $.ajax({
            url: listingUrl,
            data: {p: page},
            dataType: "html",
            success: function(data, status, xhr) {
                var response = eval('(' + data + ')');
                $(modal.body).html(response.html);
                if (response.onload) {
                    response.onload(self);
                }
                ajaxifyLinks($('#snippet-chooser-list'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

}
