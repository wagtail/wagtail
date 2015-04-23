$(function(){
    // Redirect users that don't support filereader
    if(!$('html').hasClass('filereader')){
        // TODO: Display an alternate button linking to the single uploader for users without filereader
        
        // document.location.href = window.fileupload_opts.simple_upload_url;
        // return false;
    }

    // prevents browser default drag/drop
    $(document).bind('drop dragover', function (e) {
        e.preventDefault();
    });

    $('#fileupload').fileupload({
        addUploadsTo: $(window.fileupload_opts.add_uploads_to),
        dataType: 'html',
        sequentialUploads: true,
        dropZone: $('.drop-zone'),
        acceptFileTypes: window.fileupload_opts.accepted_file_types,
        maxFileSize: window.fileupload_opts.max_file_size,
        previewMinWidth: 150,
        previewMaxWidth: 150,
        previewMinHeight: 150,
        previewMaxHeight: 150,
        messages: {
            acceptFileTypes: window.fileupload_opts.errormessages.accepted_file_types,
            maxFileSize: window.fileupload_opts.errormessages.max_file_size
        },
        add: function (e, data) {
            var $this = $(this);
            var that = $this.data('blueimp-fileupload') || $this.data('fileupload')
            var li = $($('#upload-list-item').html()).addClass('upload-uploading')
            var options = that.options;

            options.addUploadsTo.prepend(li);
            data.context = li;

            data.process(function () {
                return $this.fileupload('process', data);
            }).always(function () {
                data.context.removeClass('processing');
                // data.context.find('.left').each(function(index, elm){
                //     $(elm).append(data.files[index].name);
                // });
                data.context.find('.image').each(function (index, elm) {
                    $(elm).addClass('hasthumb')
                    $(elm).append(data.files[index].preview);
                });
            }).done(function () {
                data.context.find('.start').prop('disabled', false);
                if ((that._trigger('added', e, data) !== false) &&
                        (options.autoUpload || data.autoUpload) &&
                        data.autoUpload !== false) {
                    data.submit()
                }
            }).fail(function () {
                if (data.files.error) {
                    console.log(data)

                    data.context.each(function (index) {
                        var error = data.files[index].error;
                        if (error) {
                            $(this).find('.error_messages').text(options.messages[error]);
                        }
                    });
                }
            });
        },

        processfail: function(e, data){
            var itemElement = $(data.context);
            itemElement.removeClass('upload-uploading').addClass('upload-failure');
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
            var response = $.parseJSON(data.result);

            if(response.success){   
                itemElement.addClass('upload-success');
                itemElement.empty().append(response.content);
            } else {
                itemElement.addClass('upload-failure');
                $('.error_messages', itemElement).append(response.error_message);
            }          

        },
      
        fail: function(e, data){
            var itemElement = $(data.context);
            itemElement.addClass('upload-failure');
        },

        always: function(e, data){
            var itemElement = $(data.context);
            itemElement.removeClass('upload-uploading').addClass('upload-complete');
        },
    });
});