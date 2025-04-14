$(function () {
  console.log('Initializing bulk upload fields...');

  // Initialize Stimulus controllers for bulk upload fields
  const fileFields = document.querySelectorAll('[data-bulk-upload-file]');
  fileFields.forEach((fileField) => {
    console.log('Setting up w-sync controller for file field:', fileField);
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
    console.log('Setting up w-clean controller for title field:', titleField);
    titleField.setAttribute('data-controller', 'w-clean');
    titleField.setAttribute('data-action', 'blur->w-clean#slugify');
  });

  console.log('Initializing fileupload plugin...');
  $('#fileupload').fileupload({
    dataType: 'html',
    sequentialUploads: true,
    dropZone: $('.drop-zone'),
    previewMinWidth: 150,
    previewMaxWidth: 150,
    previewMinHeight: 150,
    previewMaxHeight: 150,
    add: function (e, data) {
      console.log('File upload started. Adding file to upload list.');
      var $this = $(this);
      var that = $this.data('blueimp-fileupload') || $this.data('fileupload');
      var li = $($('#upload-list-item').html()).addClass('upload-uploading');
      var options = that.options;

      $('#upload-list').append(li);
      data.context = li;

      data
        .process(function () {
          console.log('Processing file:', data.files[0].name);
          return $this.fileupload('process', data);
        })
        .always(function () {
          console.log('File processing complete.');
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
          console.log('File processed successfully.');
          data.context.find('.start').prop('disabled', false);
          if (
            that._trigger('added', e, data) !== false &&
            (options.autoUpload || data.autoUpload) &&
            data.autoUpload !== false
          ) {
            console.log('Auto-uploading file.');
            data.submit();
          }
        })
        .fail(function () {
          console.log('File processing failed.');
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
      console.log('Preparing form data for submission.');
      // let Stimulus handle the title generation
      return form.serializeArray();
    },

    done: function (e, data) {
      console.log('File upload successful.');
      var itemElement = $(data.context);
      var response = JSON.parse(data.result);

      if (response.success) {
        if (response.duplicate) {
          console.log('Duplicate file detected.');
          itemElement.addClass('upload-duplicate');
          $('.right', itemElement).append(response.confirm_duplicate_upload);
          $('.confirm-duplicate-upload', itemElement).on(
            'click',
            '.confirm-upload',
            function (event) {
              console.log('Confirming duplicate upload.');
              event.preventDefault();
              var confirmUpload = $(this).closest('.confirm-duplicate-upload');
              confirmUpload.remove();
              $('.right', itemElement).append(response.form);
            },
          );
        } else {
          console.log('File upload completed successfully.');
          itemElement.addClass('upload-success');
          $('.right', itemElement).append(response.form);
        }
      } else {
        console.log('File upload failed:', response.error_message);
        itemElement.addClass('upload-failure');
        $('.right .error_messages', itemElement).append(response.error_message);
      }
    },

    fail: function (e, data) {
      console.log('File upload failed due to server error:', data.errorThrown);
      var itemElement = $(data.context);
      var errorMessage = $('.server-error', itemElement);
      $('.error-text', errorMessage).text(data.errorThrown);
      $('.error-code', errorMessage).text(data.jqXHR.status);

      itemElement.addClass('upload-server-error');
    },

    always: function (e, data) {
      console.log('File upload process completed.');
      var itemElement = $(data.context);
      itemElement.removeClass('upload-uploading').addClass('upload-complete');
    },
  });

  console.log('Binding form submission handlers...');
  /**
   * ajax-enhance forms added on done()
   * allows the user to modify the title, collection, tags and delete after upload
   */
  $('#upload-list').on('submit', 'form', function (e) {
    console.log('Processing form submission.');
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
        console.log('Form submission successful.');
        var text = $('.status-msg.update-success').first().text();
        document.dispatchEvent(
          new CustomEvent('w-messages:add', {
            detail: { clear: true, text, type: 'success' },
          }),
        );
        itemElement.slideUp(function () {
          console.log('Removing item from upload list.');
          $(this).remove();
        });
      } else {
        console.log('Form submission failed, updating form.');
        form.replaceWith(data.form);
      }
    });
  });

  console.log('Binding delete handlers...');
  $('#upload-list').on('click', '.delete', function (e) {
    console.log('Delete button clicked.');
    var form = $(this).closest('form');
    var itemElement = form.closest('#upload-list > li');

    e.preventDefault();

    var CSRFToken = $('input[name="csrfmiddlewaretoken"]', form).val();

    $.post(this.href, { csrfmiddlewaretoken: CSRFToken }, function (data) {
      if (data.success) {
        console.log('File deletion successful.');
        itemElement.slideUp(function () {
          console.log('Removing item from upload list.');
          $(this).remove();
        });
      }
    });
  });

  console.log('Initialization complete.');
});
