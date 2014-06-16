$(function () {

    function process_result(data) {
        var result = $.parseJSON(data);
        if (result.success) {
            $('li#image-'+result.image_id).slideUp(function() { $(this).remove(); });
        }
    }

    $('#fileupload').fileupload({
        dataType: 'html',
        sequentialUploads: true,
        done: function (e, data) {
            var im_li = $(data.result);

            im_li.find('form').each(function() {

                var jform = $(this);

                jform.submit(function(event) { //convert save to an ajax call
                    event.preventDefault();
                    $.post(this.action, $(this).serialize(), process_result);
                });

                jform.find('a').each(function(){ //convert delete to an ajax call
                    $(this).click(function(event) {
                        event.preventDefault();
                        $.post(this.href, jform.serialize(), process_result);
                    });

                });

                jform.find('#id_'+ im_li.attr('id') +'-tags').tagit(window.tagit_opts);
            });

            im_li
            $("#image-forms").append(im_li);
        }
    });
});