$(function () {
  console.log('[Documents] Initializing bulk upload form');

  const fileFields = document.querySelectorAll('[data-bulk-upload-file]');
  fileFields.forEach((fileField) => {
    console.log('[Documents] Setting up w-sync controller for file field', fileField);
    fileField.setAttribute('data-controller', 'w-sync');
    fileField.setAttribute('data-action', 'change->w-sync#apply');
    fileField.setAttribute('data-w-sync-target-value', '[data-bulk-upload-title]');
    fileField.setAttribute('data-w-sync-normalize-value', 'true');
    fileField.setAttribute('data-w-sync-name-value', 'wagtail:documents-upload');
  });

  const titleFields = document.querySelectorAll('[data-bulk-upload-title]');
  titleFields.forEach((titleField) => {
    console.log('[Documents] Setting up w-clean controller for title field', titleField);
    titleField.setAttribute('data-controller', 'w-clean');
    titleField.setAttribute('data-action', 'blur->w-clean#slugify');
  });

  $('#fileupload').fileupload({
    dataType: 'html',
    sequentialUploads: true,
    dropZone: $('.drop-zone'),

    add: function (e, data) {
      console.group('[Documents] File added to queue');
      console.log('Files:', data.files);
      
      var $this = $(this);
      var that = $this.data('blueimp-fileupload') || $this.data('fileupload');
      var li = $($('#upload-list-item').html()).addClass('upload-uploading');
      var options = that.options;

      console.log('[Documents] Creating upload list item');
      $('#upload-list').append(li);
      data.context = li;

      data.process(function () {
          console.log('[Documents] Processing file validation');
          return $this.fileupload('process', data);
        })
        .always(function () {
          console.log('[Documents] File processing completed');
          data.context.removeClass('processing');
          data.context.find('.left').each(function (index, elm) {
            $(elm).append(escapeHtml(data.files[index].name));
          });
        })
        .done(function () {
          console.log('[Documents] File validation successful');
          data.context.find('.start').prop('disabled', false);
          if (that._trigger('added', e, data) !== false &&
              (options.autoUpload || data.autoUpload) &&
              data.autoUpload !== false) {
            console.log('[Documents] Auto-submitting file');
            data.submit();
          }
        })
        .fail(function () {
          console.error('[Documents] File validation failed');
          if (data.files.error) {
            data.context.each(function (index) {
              var error = data.files[index].error;
              if (error) {
                $(this).find('.error_messages').text(error);
              }
            });
          }
        });
      console.groupEnd();
    },

    processfail: function (e, data) {
      console.error('[Documents] File processing failed', data.files[0].error);
      var itemElement = $(data.context);
      itemElement.removeClass('upload-uploading').addClass('upload-failure');
    },

    progress: function (e, data) {
      if (e.isDefaultPrevented()) {
        return false;
      }

      var progress = Math.floor((data.loaded / data.total) * 100);
      console.log(`[Documents] Upload progress for file: ${progress}%`);
      
      data.context.each(function () {
        $(this)
          .find('.progress')
          .addClass('active')
          .attr('aria-valuenow', progress)
          .find('.bar')
          .css('width', progress + '%')
          .html(progress + '%');
      });
    },

    progressall: function (e, data) {
      var progress = parseInt((data.loaded / data.total) * 100, 10);
      console.log(`[Documents] Total upload progress: ${progress}%`);
      
      $('#overall-progress')
        .addClass('active')
        .attr('aria-valuenow', progress)
        .find('.bar')
        .css('width', progress + '%')
        .html(progress + '%');

      if (progress >= 100) {
        console.log('[Documents] All files completed uploading');
        $('#overall-progress')
          .removeClass('active')
          .find('.bar')
          .css('width', '0%');
      }
    },

    formData: function (form) {
      console.log('[Documents] Preparing form data', form.serializeArray());
      return form.serializeArray();
    },

    done: function (e, data) {
      console.group('[Documents] File upload completed');
      var itemElement = $(data.context);
      var response = JSON.parse(data.result);
      console.log('Server response:', response);

      if (response.success) {
        console.log('[Documents] Upload successful');
        itemElement.addClass('upload-success');
        $('.right', itemElement).append(response.form);
      } else {
        console.error('[Documents] Upload failed', response.error_message);
        itemElement.addClass('upload-failure');
        $('.right .error_messages', itemElement).append(response.error_message);
      }
      console.groupEnd();
    },

    fail: function (e, data) {
      console.error('[Documents] File upload failed', data.errorThrown);
      var itemElement = $(data.context);
      itemElement.addClass('upload-failure');
    },

    always: function (e, data) {
      console.log('[Documents] Upload process completed (success or failure)');
      var itemElement = $(data.context);
      itemElement.removeClass('upload-uploading').addClass('upload-complete');
    }
  });

  // Enhanced logging for form submissions
  $('#upload-list').on('submit', 'form', function (e) {
    console.group('[Documents] Processing form update');
    var form = $(this);
    var formData = new FormData(this);
    var itemElement = form.closest('#upload-list > li');

    e.preventDefault();
    console.log('Form data:', Object.fromEntries(formData));

    $.ajax({
      contentType: false,
      data: formData,
      processData: false,
      type: 'POST',
      url: this.action,
    }).done(function (data) {
      console.log('[Documents] Form update response', data);
      if (data.success) {
        console.log('[Documents] Update successful');
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
        console.log('[Documents] Update failed, showing form errors');
        form.replaceWith(data.form);
      }
    }).fail(function (xhr, status, error) {
      console.error('[Documents] Form update failed', status, error);
    });
    console.groupEnd();
  });

  // Enhanced logging for delete operations
  $('#upload-list').on('click', '.delete', function (e) {
    console.group('[Documents] Processing delete request');
    var form = $(this).closest('form');
    var itemElement = form.closest('#upload-list > li');

    e.preventDefault();
    console.log('Delete URL:', this.href);

    var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();

    $.post(this.href, { csrfmiddlewaretoken: CSRFToken }, function (data) {
      console.log('[Documents] Delete response', data);
      if (data.success) {
        console.log('[Documents] Delete successful');
        itemElement.slideUp(function () {
          $(this).remove();
        });
      }
    }).fail(function (xhr, status, error) {
      console.error('[Documents] Delete failed', status, error);
    });
    console.groupEnd();
  });

  document.addEventListener('sync:complete', (e) => {
    console.log('[Stimulus] w-sync completed:', e.detail);
  });

  document.addEventListener('sync:error', (e) => {
    console.error('[Stimulus] w-sync error:', e.detail);
  });

  document.addEventListener('cleaned', (e) => {
    console.log('[Stimulus] w-clean completed:', e.target.value);
  });

  console.log('[Documents] Bulk upload initialization complete');
});
