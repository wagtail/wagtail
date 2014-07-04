toggle = function (link) {
    $(document).on('click', link, function () {
        a = this;
        $.ajax({
            type: 'POST',
            url: a.href,
            data: { csrfmiddlewaretoken: $.cookie('csrftoken') },
            success: function (data) {
                // update
                $(a).parent().replaceWith(data);
            }
        });
        return false;   // return false to avoid jump to this link
    });
};
