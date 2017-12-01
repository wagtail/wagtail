$(function() {
    // Redirect users that don't support filereader
    if (!$('html').hasClass('filereader')) {
        document.location.href = window.fileupload_opts.simple_upload_url;
        return false;
    }

    // prevents browser default drag/drop
    $(document).on('drop dragover', function(e) {
        e.preventDefault();
    });

    $('#fileupload').fileupload({
        dataType: 'html',
        sequentialUploads: true,
        dropZone: $('.drop-zone'),
        add: function(e, data) {
            var $this = $(this);
            var that = $this.data('blueimp-fileupload') || $this.data('fileupload')
            var li = $($('#upload-list-item').html()).addClass('upload-uploading')
            var options = that.options;

            $('#upload-list').append(li);
            data.context = li;

            data.process(function() {
                return $this.fileupload('process', data);
            }).always(function() {
                data.context.removeClass('processing');
                data.context.find('.left').each(function(index, elm) {
                    $(elm).append(escapeHtml(data.files[index].name));
                });

            }).done(function() {
                data.context.find('.start').prop('disabled', false);
                if ((that._trigger('added', e, data) !== false) &&
                        (options.autoUpload || data.autoUpload) &&
                        data.autoUpload !== false) {
                    data.submit()
                }
            }).fail(function() {
                if (data.files.error) {
                    data.context.each(function(index) {
                        var error = data.files[index].error;
                        if (error) {
                            $(this).find('.error_messages').text(error);
                        }
                    });
                }
            });
        },

        processfail: function(e, data) {
            var itemElement = $(data.context);
            itemElement.removeClass('upload-uploading').addClass('upload-failure');
        },

        progress: function(e, data) {
            if (e.isDefaultPrevented()) {
                return false;
            }

            var progress = Math.floor(data.loaded / data.total * 100);
            data.context.each(function() {
                $(this).find('.progress').addClass('active').attr('aria-valuenow', progress).find('.bar').css(
                    'width',
                    progress + '%'
                ).html(progress + '%');
            });
        },

        progressall: function(e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#overall-progress').addClass('active').attr('aria-valuenow', progress).find('.bar').css(
                'width',
                progress + '%'
            ).html(progress + '%');

            if (progress >= 100) {
                $('#overall-progress').removeClass('active').find('.bar').css('width', '0%');
            }
        },

        done: function(e, data) {
            var itemElement = $(data.context);
            var response = JSON.parse(data.result);

            if (response.success) {
                itemElement.addClass('upload-success')

                $('.right', itemElement).append(response.form);
            } else {
                itemElement.addClass('upload-failure');
                $('.right .error_messages', itemElement).append(response.error_message);
            }

        },

        fail: function(e, data) {
            var itemElement = $(data.context);
            itemElement.addClass('upload-failure');
        },

        always: function(e, data) {
            var itemElement = $(data.context);
            itemElement.removeClass('upload-uploading').addClass('upload-complete');
        }
    });

    // ajax-enhance forms added on done()
    $('#upload-list').on('submit', 'form', function(e) {
        var form = $(this);
        var itemElement = form.closest('#upload-list > li');

        e.preventDefault();

        $.post(this.action, form.serialize(), function(data) {
            if (data.success) {
                itemElement.slideUp(function() {$(this).remove()});
            } else {
                form.replaceWith(data.form);

                // run tagit enhancement on new form
                $('.tag_field input', form).tagit(window.tagit_opts);
            }
        });
    });

    $('#upload-list').on('click', '.delete', function(e) {
        var form = $(this).closest('form');
        var itemElement = form.closest('#upload-list > li');

        e.preventDefault();

        var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();

        $.post(this.href, {csrfmiddlewaretoken: CSRFToken}, function(data) {
            if (data.success) {
                itemElement.slideUp(function() {$(this).remove()});
            }
        });
    });

});
