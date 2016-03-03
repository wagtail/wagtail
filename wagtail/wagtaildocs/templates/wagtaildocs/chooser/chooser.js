{% load i18n %}
function(modal) {
    function ajaxifyLinks (context) {
        $('a.document-choice', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    };

    var searchUrl = $('form.document-search', modal.body).attr('action');
    function search() {
        $.ajax({
            url: searchUrl,
            data: {
                q: $('#id_q').val(),
                collection_id: $('#collection_chooser_collection_id').val()
            },
            success: function(data, status) {
                $('#search-results').html(data);
                ajaxifyLinks($('#search-results'));
            }
        });
        return false;
    };
    function setPage(page) {

        if($('#id_q').val().length){
            dataObj = {q: $('#id_q').val(), p: page};
        }else{
            dataObj = {p: page};
        }

        $.ajax({
            url: searchUrl,
            data: dataObj,
            success: function(data, status) {
                $('#search-results').html(data);
                ajaxifyLinks($('#search-results'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

    $('form.document-upload', modal.body).submit(function() {
        var formdata = new FormData(this);

        $.ajax({
            url: this.action,
            data: formdata,
            processData: false,
            contentType: false,
            type: 'POST',
            dataType: 'text',
            success: function(response){
                modal.loadResponseText(response);
            },
            error: function(response, textStatus, errorThrown) {
                {% trans "Server Error" as error_label %}
                {% trans "Report this error to your webmaster with the following information:" as error_message %}
                message = '{{ error_message|escapejs }}<br />' + errorThrown + ' - ' + response.status;
                $('#upload').append(
                    '<div class="help-block help-critical">' +
                    '<strong>{{ error_label|escapejs }}: </strong>' + message + '</div>');
            }
        });

        return false;
    });

    $('form.document-search', modal.body).submit(search);

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 50);
        $(this).data('timer', wait);
    });

    $('#collection_chooser_collection_id').change(search);

    {% url 'wagtailadmin_tag_autocomplete' as autocomplete_url %}
    $('#id_tags', modal.body).tagit({
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    });
}
