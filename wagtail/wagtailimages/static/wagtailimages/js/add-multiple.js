$(function(){
    function process_result(data) {
        var result = $.parseJSON(data);
        if (result.success) {
            $('li#image-'+result.image_id).slideUp(function() { $(this).remove(); });
        }
    }

    // prevents browser default drag/drop
    $(document).bind('drop dragover', function (e) {
        e.preventDefault();
    });

    $('#fileupload').fileupload({
        dataType: 'html',
        sequentialUploads: true,
        dropZone: $('.drop-zone'),
        acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
        previewMinWidth:150,
        previewMaxWidth:150,
        previewMinHeight:150,
        previewMaxHeight:150,   

        add: function (e, data) {
            var $this = $(this);
            var that = $this.data('blueimp-fileupload') || $this.data('fileupload')
            var li = $($('#upload-list-item').html()).addClass('uploading')
            var options = that.options;

            $('#upload-list').append(li);
            data.context = li;
           
            data.process(function () {
                return $this.fileupload('process', data);
            }).always(function () {
                data.context.removeClass('processing');
                data.context.find('.preview .thumb').each(function (index, elm) {
                    $(elm).addClass('hasthumb')
                    $(elm).append(data.files[index].preview);
                });
            }).done(function () {
                data.context.find('.start').prop('disabled', false);
                if ((that._trigger('added', e, data) !== false) &&
                        (options.autoUpload || data.autoUpload) &&
                        data.autoUpload !== false) {
                    data.submit();
                }
            }).fail(function () {
                if (data.files.error) {
                    data.context.each(function (index) {
                        var error = data.files[index].error;
                        if (error) {
                            $(this).find('.error').text(error);
                        }
                    });
                }
            });

        },
        
        progress: function (e, data) {
            if (e.isDefaultPrevented()) {
                return false;
            }

            var progress = Math.floor(data.loaded / data.total * 100);
            data.context.each(function () {
                $(this).find('.progress').attr('aria-valuenow', progress).find('.bar').css(
                    'width',
                    progress + '%'
                );
            });
        },
        
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#overall-progress').attr('aria-valuenow', progress).find('.bar').css(
                'width',
                progress + '%'
            );
        },
        
        done: function (e, data) {
            var itemElement = $(data.context);
            $('.right', itemElement).append(data.result).addClass('done');

            $('form', itemElement).each(function(){
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

                //jform.find('#id_'+ im_li.attr('id') +'-tags').tagit(window.tagit_opts);
            });
        },
      
        fail: function(e, data){
            var itemElement = $(data.context);
            itemElement.addClass('failed');
        },

        always: function(e, data){
            var itemElement = $(data.context);
            itemElement.removeClass('uploading');
        },
    });
});