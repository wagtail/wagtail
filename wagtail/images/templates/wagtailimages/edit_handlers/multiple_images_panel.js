{% load l10n %}
{% load wagtailadmin_tags %}

{% url 'wagtailadmin_tag_autocomplete' as autocomplete_url %}

(function() {
    var panel = InlinePanel({
        formsetPrefix: "id_{{ self.formset.prefix }}",
        emptyChildFormPrefix: "{{ self.empty_child.form.prefix }}",
        canOrder: {% if can_order %}true{% else %}false{% endif %},
        maxForms: {{ self.formset.max_num|unlocalize }}
    });

    {% for child in self.children %}
        panel.initChildControls("{{ child.form.prefix }}");
    {% endfor %}
    panel.setHasContent();
    panel.updateMoveButtonDisabledStates();
    panel.updateAddButtonState();


    window.fileupload_opts = {
        simple_upload_url: "{% url 'wagtailimages:add' %}",
        accepted_file_types: /\.({{ allowed_extensions|join:"|" }})$/i, //must be regex
        max_file_size: {{ max_filesize|stringformat:"s"|default:"null" }}, //numeric format
        errormessages: {
            max_file_size: "{{ error_max_file_size }}",
            accepted_file_types: "{{ error_accepted_file_types }}"
        }
    }
    window.tagit_opts = {
        autocomplete: {source: "{{ autocomplete_url|addslashes }}"}
    };

    $('#{{self.formset.prefix}}-fileupload').fileupload({
        dataType: 'html',
        url: $('#{{self.formset.prefix}}-fileupload').data('url'),
        sequentialUploads: true,
        dropZone: $('.drop-zone'),
        acceptFileTypes: window.fileupload_opts.accepted_file_types,
        maxFileSize: window.fileupload_opts.max_file_size,
        previewMinWidth:150,
        previewMaxWidth:150,
        previewMinHeight:150,
        previewMaxHeight:150,
        messages: {
            acceptFileTypes: window.fileupload_opts.errormessages.accepted_file_types,
            maxFileSize: window.fileupload_opts.errormessages.max_file_size
        },
        add: function(e, data) {
            $('.messages').empty();
            var $this = $(this);
            var that = $this.data('blueimp-fileupload') || $this.data('fileupload')
            var li = $($('#{{self.formset.prefix}}-upload-list-item').html()).addClass('upload-uploading')
            var options = that.options;

            $('#{{self.formset.prefix}}-upload-list').append(li);
            data.context = li;

            data.process(function() {
                return $this.fileupload('process', data);
            }).always(function() {
                data.context.removeClass('processing');
                data.context.find('.left').each(function(index, elm) {
                    $(elm).append(escapeHtml(data.files[index].name));
                });

                data.context.find('.preview .thumb').each(function(index, elm) {
                    $(elm).addClass('hasthumb')
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
            $('#{{self.formset.prefix}}-overall-progress').addClass('active').attr('aria-valuenow', progress).find('.bar').css(
                'width',
                progress + '%'
            ).html(progress + '%');

            if (progress >= 100) {
                $('#{{self.formset.prefix}}-overall-progress').removeClass('active').find('.bar').css('width', '0%');
            }
        },

        done: function(e, data) {
            var itemElement = $(data.context);
            var response = JSON.parse(data.result);

            if (response.success) {
                itemElement.addClass('upload-success');
                var prefixId = panel.addOne();
                var imageField = $('#id_{{ self.formset.prefix }}-'+prefixId+'-{{self.image_field_name}}');
                var imageChosen = imageField.data('imageChooser');
                imageChosen(response.image);

            } else {
                itemElement.addClass('upload-failure');
                $('.right .error_messages', itemElement).append(response.error_message);
            }

        },

        fail: function(e, data) {
            var itemElement = $(data.context);
            var errorMessage = $('.server-error', itemElement);
            $('.error-text', errorMessage).text(data.errorThrown);
            $('.error-code', errorMessage).text(data.jqXHR.status);

            itemElement.addClass('upload-server-error');
        },

        always: function(e, data) {
            var itemElement = $(data.context);
            itemElement.removeClass('upload-uploading').addClass('upload-complete');
        }
    });

    // ajax-enhance forms added on done()
    $('#{{self.formset.prefix}}-upload-list').on('submit', 'form', function(e) {
        var form = $(this);
        var itemElement = form.closest('#{{self.formset.prefix}}-upload-list > li');

        e.preventDefault();

        $.post(this.action, form.serialize(), function(data) {
            if (data.success) {
                var statusText = $('.status-msg.update-success').text();
                addMessage('success', statusText);
                itemElement.slideUp(function() {$(this).remove()});
            } else {
                form.replaceWith(data.form);

                // run tagit enhancement on new form
                $('.tag_field input', form).tagit(window.tagit_opts);
            }
        });
    });

    $('#{{self.formset.prefix}}-upload-list').on('click', '.delete', function(e) {
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

})();
