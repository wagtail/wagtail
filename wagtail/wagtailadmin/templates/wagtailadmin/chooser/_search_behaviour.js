modal.ajaxifyForm($('form.search-form', modal.body));

var searchUrl = $('form.search-form', modal.body).attr('action');

function search() {
    $.ajax({
        url: searchUrl,
        data: {
            q: $('#id_q', modal.body).val(),
            results_only: true
        },
        success: function(data, status) {
            $('.page-results', modal.body).html(data);
            ajaxifySearchResults();
        }
    });
    return false;
}

$('#id_q', modal.body).on('input', function() {
    clearTimeout($.data(this, 'timer'));
    var wait = setTimeout(search, 200);
    $(this).data('timer', wait);
});

function ajaxifySearchResults() {
    $('.page-results a.choose-page', modal.body).click(function() {
        var pageData = $(this).data();
        modal.respond('pageChosen', $(this).data());
        modal.close();

        return false;
    });
}

$('#id_q', modal.body).focus();
