function(modal) {
    var searchUrl = $('form.image-search', modal.body).attr('action');

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

    function search() {
        $.ajax({
            url: searchUrl,
            data: {q: $('#id_q').val()},
            success: function(data, status) {
                $('#image-results').html(data);
                ajaxifyLinks($('#image-results'));
            }
        });
        return false;
    }

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
                $('#image-results').html(data);
                ajaxifyLinks($('#image-results'));
            }
        });
        return false;
    }

    ajaxifyLinks(modal.body);

    $('form.image-upload', modal.body).submit(function() {
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
            }
        });

        return false;
    });

    $('form.image-search', modal.body).submit(search);

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 200);
        $(this).data('timer', wait);
    });
    $('a.suggested-tag').click(function() {
        $('#id_q').val($(this).text());
        search();
        return false;
    });

    {% url 'wagtailadmin_tag_autocomplete' as autocomplete_url %}
    
    /* Add tag entry interface (with autocompletion) to the tag field of the image upload form */
    $('#id_tags', modal.body).tagit({
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    });
}
