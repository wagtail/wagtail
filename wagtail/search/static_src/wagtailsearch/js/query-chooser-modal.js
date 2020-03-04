QUERY_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'chooser': function(modal, jsonData) {
        function ajaxifyLinks (context) {

            $('.listing a.choose-query', context).on('click', chooseQuery);

            $('.pagination a', context).on('click', function() {
                var page = this.getAttribute("data-page");
                setPage(page);
                return false;
            });
        }

        var searchUrl = $('form.query-search', modal.body).attr('action');
        var request;

        function search() {
            request = $.ajax({
                url: searchUrl,
                data: {q: $('#id_q').val()},
                success: function(data, status) {
                    request = null;
                    $('#query-results').html(data);
                    ajaxifyLinks($('#query-results'));
                },
                error: function() {
                    request = null;
                }
            });
            return false;
        }
        function setPage(page) {
            var dataObj;

            if($('#id_q').val().length){
                dataObj = {q: $('#id_q').val(), p: page};
            }else{
                dataObj = {p: page};
            }

            request = $.ajax({
                url: searchUrl,
                data: dataObj,
                success: function(data, status) {
                    request = null;
                    $('#query-results').html(data);
                    ajaxifyLinks($('#query-results'));
                },
                error: function() {
                    request = null;
                }
            });
            return false;
        }
        function chooseQuery() {
            modal.respond('queryChosen', $(this).data());
            modal.close();

            return false;
        }

        ajaxifyLinks(modal.body);

        $('form.query-search', modal.body).on('submit', search);

        $('#id_q').on('input', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 200);
            $(this).data('timer', wait);
        });
    }
};
