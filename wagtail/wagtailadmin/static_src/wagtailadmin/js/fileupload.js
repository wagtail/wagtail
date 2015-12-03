(function($) {
    window.Fileuploader = function(opts) {
        var initOpts;
        var opts = opts || {}

        var defaultOpts = {
            // implementation opts unique to Wagtail
            field: $('.fileupload'),
            addUploadsTo: $('body'),
            newItemContainer: $('<div></div>'),
            supported: null,
            unsupported: null,
            onItemComplete: null,

            // standard fileupload opts
            dataType: 'html',
            sequentialUploads: true,
            dropZone: $('.drop-zone'),
            acceptFileTypes: null,
            maxFileSize: 0,
            previewMinWidth: 150,
            previewMaxWidth: 150,
            previewMinHeight: 150,
            previewMaxHeight: 150,
            messages: {
                acceptFileTypes: '',
                maxFileSize: ''
            },

            add: function(e, data) {
                var $this = $(this);
                var that = $this.data('blueimp-fileupload') || $this.data('fileupload')
                var options = that.options;
                var newItem = $(options.newItemContainer.html()).addClass('upload-uploading');

                options.addUploadsTo.prepend(newItem);
                data.context = newItem;

                data.process(function() {
                    return $this.fileupload('process', data);
                }).always(function() {
                    data.context.find('.image').each(function(index, elm) {
                        $(elm).append(data.files[index].preview);
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
                                addMessage('error', error);
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
                var response = $.parseJSON(data.result);
                var that = $(this).data('blueimp-fileupload') || $(this).data('fileupload')

                if (response.success) {
                    itemElement.empty().append(response.content).addClass('upload-success');
                    that.options.onItemComplete(data);
                } else {
                    itemElement.addClass('upload-failure');
                    addMessage('error', response.error_message);
                }
            },

            fail: function(e, data) {
                var itemElement = $(data.context);
                itemElement.removeClass('upload-uploading').addClass('upload-failure');
                addMessage('error', data.errorThrown.toLowerCase());
            },

            always: function(e, data) {
                var itemElement = $(data.context);
                itemElement.removeClass('upload-uploading').addClass('upload-complete');
            }
        }

        initOpts = $.extend(defaultOpts, opts);

        if ($('html').hasClass('filereader')) {
            // prevents browser default drag/drop
            $(document).bind('drop dragover', function(e) {
                e.preventDefault();
            });

            if (initOpts.supported) {
                initOpts.supported();
            }

            return $(initOpts.field).fileupload(initOpts);
        } else {
            if (initOpts.unsupported) {
                initOpts.unsupported();
            }

            return false;
        }
    }
})(jQuery);