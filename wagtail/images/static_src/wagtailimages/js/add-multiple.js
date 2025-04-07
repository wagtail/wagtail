$(function () {
  // initialize Stimulus controllers for bulk upload fields
  const fileFields = document.querySelectorAll('[data-bulk-upload-file]');
  fileFields.forEach((fileField) => {
    fileField.setAttribute('data-controller', 'w-sync');
    fileField.setAttribute('data-action', 'change->w-sync#apply');
    fileField.setAttribute(
      'data-w-sync-target-value',
      '[data-bulk-upload-title]',
    );
    fileField.setAttribute('data-w-sync-normalize-value', 'true');
    fileField.setAttribute('data-w-sync-name-value', 'wagtail:images-upload');
  });

  const titleFields = document.querySelectorAll('[data-bulk-upload-title]');
  titleFields.forEach((titleField) => {
    titleField.setAttribute('data-controller', 'w-clean');
    titleField.setAttribute('data-action', 'blur->w-clean#slugify');
  });

  $('#fileupload').fileupload({
    dataType: 'html',
    sequentialUploads: true,
    dropZone: $('.drop-zone'),
    previewMinWidth: 150,
    previewMaxWidth: 150,
    previewMinHeight: 150,
    previewMaxHeight: 150,
    add: function (e, data) {
      var $this = $(this);
      var that = $this.data('blueimp-fileupload') || $this.data('fileupload');
      var li = $($('#upload-list-item').html()).addClass('upload-uploading');
      var options = that.options;

      $('#upload-list').append(li);
      data.context = li;

      data
        .process(function () {
          return $this.fileupload('process', data);
        })
        .always(function () {
          data.context.removeClass('processing');
          data.context.find('.left').each(function (index, elm) {
            $(elm).append(escapeHtml(data.files[index].name));
          });

          data.context.find('.preview .thumb').each(function (index, elm) {
            $(elm).find('.icon').remove();
            $(elm).append(data.files[index].preview);
          });
        })
        .done(function () {
          data.context.find('.start').prop('disabled', false);
          if (
            that._trigger('added', e, data) !== false &&
            (options.autoUpload || data.autoUpload) &&
            data.autoUpload !== false
          ) {
            data.submit();
          }
        })
        .fail(function () {
          if (data.files.error) {
            data.context.each(function (index) {
              var error = data.files[index].error;
              if (error) {
                $(this).find('.error_messages').html(error);
              }
            });
          }
        });
    },

    formData: function (form) {
      // let Stimulus handle the title generation
      return form.serializeArray();
    },

    done: function (e, data) {
      var itemElement = $(data.context);
      var response = JSON.parse(data.result);

      if (response.success) {
        if (response.duplicate) {
          itemElement.addClass('upload-duplicate');
          $('.right', itemElement).append(response.confirm_duplicate_upload);
          $('.confirm-duplicate-upload', itemElement).on(
            'click',
            '.confirm-upload',
            function (event) {
              event.preventDefault();
              var confirmUpload = $(this).closest('.confirm-duplicate-upload');
              confirmUpload.remove();
              $('.right', itemElement).append(response.form);
            },
          );
        } else {
          itemElement.addClass('upload-success');
          $('.right', itemElement).append(response.form);
        }
      } else {
        itemElement.addClass('upload-failure');
        $('.right .error_messages', itemElement).append(response.error_message);
      }
    },

    fail: function (e, data) {
      var itemElement = $(data.context);
      var errorMessage = $('.server-error', itemElement);
      $('.error-text', errorMessage).text(data.errorThrown);
      $('.error-code', errorMessage).text(data.jqXHR.status);

      itemElement.addClass('upload-server-error');
    },

    always: function (e, data) {
      var itemElement = $(data.context);
      itemElement.removeClass('upload-uploading').addClass('upload-complete');
    },
  });

  /**
   * ajax-enhance forms added on done()
   * allows the user to modify the title, collection, tags and delete after upload
   */
  $('#upload-list').on('submit', 'form', function (e) {
    var form = $(this);
    var formData = new FormData(this);
    var itemElement = form.closest('#upload-list > li');

    e.preventDefault();

    $.ajax({
      contentType: false,
      data: formData,
      processData: false,
      type: 'POST',
      url: this.action,
    }).done(function (data) {
      if (data.success) {
        var text = $('.status-msg.update-success').first().text();
        document.dispatchEvent(
          new CustomEvent('w-messages:add', {
            detail: { clear: true, text, type: 'success' },
          }),
        );
        itemElement.slideUp(function () {
          $(this).remove();
        });
      } else {
        form.replaceWith(data.form);
      }
    });
  });

  $('#upload-list').on('click', '.delete', function (e) {
    var form = $(this).closest('form');
    var itemElement = form.closest('#upload-list > li');

    e.preventDefault();

    var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();

    $.post(this.href, { csrfmiddlewaretoken: CSRFToken }, function (data) {
      if (data.success) {
        itemElement.slideUp(function () {
          $(this).remove();
        });
      }
    });
  });
});
