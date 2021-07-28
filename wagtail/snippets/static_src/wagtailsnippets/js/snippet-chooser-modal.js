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
            var data = {q: $('#id_q').val()};

            if (searchForm$.has('input[name="locale"]')) {
                data['locale'] = $('input[name="locale"]', searchForm$).val();
            }

            if (searchForm$.has('#snippet-chooser-locale')) {
                data['locale_filter'] = $('#snippet-chooser-locale', searchForm$).val();
            }

            loadResults(searchUrl, data);
            return false;
        }

        function loadResults(url, data) {
            var opts = {
                url: url,
                success: function(data, status) {
                    request = null;
                    $('#search-results').html(data);
                    ajaxifyLinks($('#search-results'));
                },
                error: function() {
                    request = null;
                }
            }
            if (data) {
                opts.data = data;
            }
            request = $.ajax(opts);
        }

        $('form.snippet-search', modal.body).on('submit', search);

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
        modal.respond('snippetChosen', jsonData['result']);
        modal.close();
    }
};
