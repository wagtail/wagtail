SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'choose': function(modal, jsonData) {
        function ajaxifyLinks(context) {
            $('a.snippet-choice', modal.body).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            $('.pagination a', context).on('click', function() {
                loadResults(this.href);
                return false;
            });
        }

        var searchForm$ = $('form.snippet-search', modal.body);
        var searchUrl = searchForm$.attr('action');
        var request;

        function search() {
            loadResults(searchUrl, searchForm$.serialize());
            return false;
        }

        function loadResults(url, data) {
            var opts = {
                url: url,
                success: function(resultsData, status) {
                    request = null;
                    $('#search-results').html(resultsData);
                    ajaxifyLinks($('#search-results'));
                },
                error: function() {
                    request = null;
                }
            };
            if (data) {
                opts.data = data;
            }
            request = $.ajax(opts);
        }

        $('form.snippet-search', modal.body).on('submit', search);
        $('#snippet-chooser-locale', modal.body).on('change', search);

        $('#id_q').on('input', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 200);
            $(this).data('timer', wait);
        });

        ajaxifyLinks(modal.body);
    },
    'chosen': function(modal, jsonData) {
        modal.respond('snippetChosen', jsonData.result);
        modal.close();
    }
};
