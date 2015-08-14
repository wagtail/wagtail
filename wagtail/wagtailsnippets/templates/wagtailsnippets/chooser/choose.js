function initModal(modal) {

    function ajaxifyLinks(context) {
        $('a.snippet-choice', modal.body).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute('data-page');
            setPage(page);
            return false;
        });
    }

    var searchUrl = $('form.snippet-search', modal.body).attr('action');

    function setPage(page) {
        $.ajax({
            url: searchUrl,
            data: {p: page, results: 'true'},
            success: function(data, status) {
                $('#search-results').html(data);
                ajaxifyLinks($('#search-results'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

}
