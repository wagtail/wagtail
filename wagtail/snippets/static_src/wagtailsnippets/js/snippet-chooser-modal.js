SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'choose': function(modal, jsonData) {
        function ajaxifyLinks(context) {
            $('a.snippet-choice', modal.body).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            $('.pagination a', context).on('click', function() {
                var page = this.getAttribute('data-page');
                setPage(page);
                return false;
            });
        }

        var searchUrl = $('form.snippet-search', modal.body).attr('action');
        var request;

        function search() {
            request = $.ajax({
                url: searchUrl,
                data: {q: $('#id_q').val(), results: 'true'},
                success: function(data, status) {
                    request = null;
                    $('#search-results').html(data);
                    ajaxifyLinks($('#search-results'));
                },
                error: function() {
                    request = null;
                }
            });
            return false;
        }

        function setPage(page) {
            var dataObj = {p: page, results: 'true'};

            if ($('#id_q').length && $('#id_q').val().length) {
                dataObj.q = $('#id_q').val();
            }

            request = $.ajax({
                url: searchUrl,
                data: dataObj,
                success: function(data, status) {
                    request = null;
                    $('#search-results').html(data);
                    ajaxifyLinks($('#search-results'));
                },
                error: function() {
                    request = null;
                }
            });
            return false;
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
