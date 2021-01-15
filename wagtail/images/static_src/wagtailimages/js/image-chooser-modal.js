IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'chooser': function(modal, jsonData) {
        var searchUrl = $('form.image-search', modal.body).attr('action');

        /* currentTag stores the tag currently being filtered on, so that we can
        preserve this when paginating */
        var currentTag;

        function ajaxifyLinks (context) {
            $('.listing a', context).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            $('.pagination a', context).on('click', function() {
                var page = this.getAttribute("data-page");
                setPage(page);
                return false;
            });
        }
        var request;

        function fetchResults(requestData) {
            request = $.ajax({
                url: searchUrl,
                data: requestData,
                success: function(data, status) {
                    request = null;
                    $('#image-results').html(data);
                    ajaxifyLinks($('#image-results'));
                },
                error: function() {
                    request = null;
                }
            });
        }

        function search() {
            /* Searching causes currentTag to be cleared - otherwise there's
            no way to de-select a tag */
            currentTag = null;
            fetchResults({
                q: $('#id_q').val(),
                collection_id: $('#collection_chooser_collection_id').val()
            });
            return false;
        }

        function setPage(page) {
            var params = {p: page};
            if ($('#id_q').val().length){
                params['q'] = $('#id_q').val();
            }
            if (currentTag) {
                params['tag'] = currentTag;
            }
            params['collection_id'] = $('#collection_chooser_collection_id').val();
            fetchResults(params);
            return false;
        }

        ajaxifyLinks(modal.body);

        $('form.image-upload', modal.body).on('submit', function() {
            var formdata = new FormData(this);

            if ($('#id_image-chooser-upload-title', modal.body).val() == '') {
                var li = $('#id_image-chooser-upload-title', modal.body).closest('li');
                if (!li.hasClass('error')) {
                    li.addClass('error');
                    $('#id_image-chooser-upload-title', modal.body).closest('.field-content').append('<p class="error-message"><span>This field is required.</span></p>')
                }
                setTimeout(cancelSpinner, 500);
            } else {
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
            }

            return false;
        });

        $('form.image-search', modal.body).on('submit', search);

        $('#id_q').on('input', function() {
            if (request) {
                request.abort();
            }
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 200);
            $(this).data('timer', wait);
        });
        $('#collection_chooser_collection_id').on('change', search);
        $('a.suggested-tag').on('click', function() {
            currentTag = $(this).text();
            $('#id_q').val('');
            fetchResults({
                'tag': currentTag,
                collection_id: $('#collection_chooser_collection_id').val()
            });
            return false;
        });

        /* set up pre-filling of title based on selected file */
        function populateTitle(context) {
            var fileWidget = $('#id_image-chooser-upload-file', context);
            fileWidget.on('change', function (event) {
                var titleWidget = $('#id_image-chooser-upload-title', context);
                var title = titleWidget.val();
                if (title === '') {
                    // The file widget value example: `C:\fakepath\image.jpg`
                    var parts = fileWidget.val().split('\\');
                    var fileName = parts[parts.length - 1];

                    var getImageUploadTitle = window.wagtail.utils.getImageUploadTitle;

                    if (typeof getImageUploadTitle !== "function") {
                        titleWidget.val(fileName);
                        return;
                    };

                    // allow for the getImageUploadTitle global to override the provided
                    // filename with a custom title (e.g. a regex to remove the extension).

                    var maxLength = titleWidget.attr("maxLength") || null;

                    var newTitle = getImageUploadTitle(fileName, {
                        event,
                        maxLength: maxLength && parseInt(maxLength),
                        widget: "CHOOSER_MODAL",
                    });

                    // allow for the util to return null/non-string to not update title
                    if (typeof newTitle !== "string") return;

                    titleWidget.val(newTitle);
                }
            });
        }

        populateTitle(modal.body);
    },
    'image_chosen': function(modal, jsonData) {
        modal.respond('imageChosen', jsonData['result']);
        modal.close();
    },
    'select_format': function(modal) {
        $('form', modal.body).on('submit', function() {
            $.post(this.action, $(this).serialize(), modal.loadResponseText, 'text');

            return false;
        });
    }
};
