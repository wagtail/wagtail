{% load i18n %}
function(modal) {
    var searchUrl = $('form.image-search', modal.body).attr('action');

    /* currentTag stores the tag currently being filtered on, so that we can
    preserve this when paginating */
    var currentTag;

    function ajaxifyLinks (context) {
        $('.listing a', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    function fetchResults(requestData) {
        $.ajax({
            url: searchUrl,
            data: requestData,
            success: function(data, status) {
                $('#image-results').html(data);
                ajaxifyLinks($('#image-results'));
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
        params = {p: page};
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

    $('form.image-upload', modal.body).submit(function() {
        var formdata = new FormData(this);

        if ($('#id_title', modal.body).val() == '') {
            var li = $('#id_title', modal.body).closest('li');
            if (!li.hasClass('error')) {
                li.addClass('error');
                $('#id_title', modal.body).closest('.field-content').append('<p class="error-message"><span>This field is required.</span></p>')
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
                success: function(response){
                    modal.loadResponseText(response);
                }
            });
        }

        return false;
    });

    $('form.image-search', modal.body).submit(search);

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 200);
        $(this).data('timer', wait);
    });
    $('#collection_chooser_collection_id').change(search);
    $('a.suggested-tag').click(function() {
        currentTag = $(this).text();
        $('#id_q').val('');
        fetchResults({
            'tag': currentTag,
            collection_id: $('#collection_chooser_collection_id').val()
        });
        return false;
    });

    {% url 'wagtailadmin_tag_autocomplete' as autocomplete_url %}

    /* Add tag entry interface (with autocompletion) to the tag field of the image upload form */
    $('#id_tags', modal.body).tagit({
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    });
}
