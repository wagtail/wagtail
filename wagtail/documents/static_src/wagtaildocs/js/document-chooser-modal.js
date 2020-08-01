DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'chooser': function(modal, jsonData) {
        function ajaxifyLinks (context) {
            $('a.document-choice', context).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            $('.pagination a', context).on('click', function() {
                var page = this.getAttribute("data-page");
                setPage(page);
                return false;
            });

            $('a.upload-one-now').on('click', function(e) {
                // Set current collection ID at upload form tab
                let collectionId = $('#collection_chooser_collection_id').val();
                if (collectionId) {
                  $('#id_document-chooser-upload-collection').val(collectionId);
                }

                // Select upload form tab
                $('a[href="#upload"]').tab('show');
                e.preventDefault();
            });
        };

        var searchUrl = $('form.document-search', modal.body).attr('action');
        var request;
        function search() {
            request = $.ajax({
                url: searchUrl,
                data: {
                    q: $('#id_q').val(),
                    collection_id: $('#collection_chooser_collection_id').val()
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

        $('form.document-upload', modal.body).on('submit', function() {
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
                    $('#upload').append(
                        '<div class="help-block help-critical">' +
                        '<strong>' + jsonData['error_label'] + ': </strong>' + message + '</div>');
                }
            });

            return false;
        });

        $('form.document-search', modal.body).on('submit', search);

        $('#id_q').on('input', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 50);
            $(this).data('timer', wait);
        });

        $('#collection_chooser_collection_id').on('change', search);
    },
    'document_chosen': function(modal, jsonData) {
        modal.respond('documentChosen', jsonData['result']);
        modal.close();
    }
};
