TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'chooser': function(modal, jsonData) {
        function ajaxifyLinks (context) {
            $('a.task-type-choice, a.choose-different-task-type, a.task-choice', context).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            $('.pagination a', context).on('click', function() {
                var page = this.getAttribute("data-page");
                setPage(page);
                return false;
            });

            $('a.create-one-now').on('click', function(e) {
                // Select upload form tab
                $('a[href="#new"]').tab('show');
                e.preventDefault();
            });
        };

        var searchUrl = $('form.task-search', modal.body).attr('action');
        var request;
        function search() {
            request = $.ajax({
                url: searchUrl,
                data: {
                    q: $('#id_q').val(),
                    task_type: $('#id_task_type').val(),
                },
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
        };
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
                    $('#search-results').html(data);
                    ajaxifyLinks($('#search-results'));
                },
                error: function() {
                    request = null;
                }
            });
            return false;
        }

        ajaxifyLinks(modal.body);

        $('form.task-create', modal.body).on('submit', function() {
            var formdata = new FormData(this);

            $.ajax({
                url: this.action,
                data: formdata,
                processData: false,
                contentType: false,
                type: 'POST',
                dataType: 'text',
                success: modal.loadResponseText,
                error: function(response, textStatus, errorThrown) {
                    var message = jsonData['error_message'] + '<br />' + errorThrown + ' - ' + response.status;
                    $('#new').append(
                        '<div class="help-block help-critical">' +
                        '<strong>' + jsonData['error_label'] + ': </strong>' + message + '</div>');
                }
            });

            return false;
        });

        $('form.task-search', modal.body).on('submit', search);

        $('#id_q').on('input', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 50);
            $(this).data('timer', wait);
        });

        $('#id_task_type').on('change', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 50);
            $(this).data('timer', wait);
        });
    },
    'task_chosen': function(modal, jsonData) {
        modal.respond('taskChosen', jsonData['result']);
        modal.close();
    }
};
