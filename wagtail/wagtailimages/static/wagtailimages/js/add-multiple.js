$(function(){
    // Redirect users that don't support filereader
    if(!$('html').hasClass('filereader')){
        document.location.href = window.simple_upload_url;
        return false;
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
            var li = $($('#upload-list-item').html()).addClass('upload-uploading')
            var options = that.options;

            $('#upload-list').append(li);
            data.context = li;

            data.process(function () {
                return $this.fileupload('process', data);
            }).always(function () {
                data.context.removeClass('processing');
                data.context.find('.left').each(function(index, elm){
                    $(elm).append(data.files[index].name);
                });
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
                $(this).find('.progress').addClass('active').attr('aria-valuenow', progress).find('.bar').css(
                    'width',
                    progress + '%'
                ).html(progress + '%');
            });
        },
        
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#overall-progress').addClass('active').attr('aria-valuenow', progress).find('.bar').css(
                'width',
                progress + '%'
            ).html(progress + '%');

            if (progress >= 100){
                $('#overall-progress').removeClass('active').find('.bar').css('width','0%');
            }
        },
        
        done: function (e, data) {
            var itemElement = $(data.context);
            itemElement.addClass('upload-success')
            // run tagit enhancement
            $('.tag_field input', itemElement).tagit(window.tagit_opts);

            // ajax-enhance forms added on done() 
            $('#upload-list').on('submit', 'form', function(e){
                var form = $(this);
                
                e.preventDefault();

                $.post(this.action, form.serialize(), function(data) {
                    if (data.success) {
                        itemElement.slideUp(function(){$(this).remove()});
                    }else{
                        console.log(data);
                        form.replaceWith(data.form);
                        // run tagit enhancement on new form
                        $('.tag_field input', form).tagit(window.tagit_opts);
                    }
                });
            });

            $('#upload-list').on('click', '.delete', function(e){
                var form = $(this);

                e.preventDefault();

                $.post(this.href, form.serialize(), function(data) {
                    if (data.success) {
                        itemElement.slideUp(function(){$(this).remove()});
                    }else{
                    
                    }
                });
            });

        },
      
        fail: function(e, data){
            var itemElement = $(data.context);
            itemElement.addClass('upload-failure');
        },

        always: function(e, data){
            var itemElement = $(data.context);
            console.log(data);
            $('.right', itemElement).append(data.result);
            itemElement.removeClass('upload-uploading').addClass('upload-complete');
        },
    });
});