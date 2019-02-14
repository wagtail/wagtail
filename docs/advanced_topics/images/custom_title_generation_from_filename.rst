.. _image_custom_title_generation_from_filename:

Custom Title Generation From Filename
=====================================

Override how the title is set when uploading single files, multiple files or uploading a file within a chooser modal.

.. note::
    This will not apply to editing images or documents (e.g. uploading a replacement image file while editing an existing image).

``wagtail.utils.getTitleFromFilename`` can be overridden with a custom function,
the first argument is the filename (e.g. ``'some_file.jpg'``) and the second is an options object.
If the return value is a ``String`` it will replace the value in the relevant title field, otherwise it will leave the title field as is (blank or with any current value).

The options available to the function are as follows:

* ``currentTitle`` - if uploading an image in place of an existing image, the currently entered title (e.g. in a chooser modal)
* ``maxLength`` - will be the maximum length on the title form field (may not available for some forms, can be null)
* ``model`` - file upload model, can be ``'DOCUMENT'`` or ``'IMAGE'``
* ``widget`` - the type of upload widget, can be ``'ADD'``, ``'ADD_MULTIPLE'`` or ``'CHOOSER_MODAL'``

Code Example
------------

.. code-block:: python

  from django.utils.html import format_html, format_html_join
  from django.templatetags.static import static

  from wagtail.core import hooks

  @hooks.register('insert_global_admin_js')
  def get_global_admin_js():
      # remember to use double '{{' so they are not parsed as template placeholders
      return format_html(
        """
        <script>
            $(function () {{
                function getTitleFromFilename (filename, options) {{
                    if (options.currentTitle) return null; // return if there is a title already entered so it will be left unchanged

                    // model can be 'IMAGE' or 'DOCUMENT'
                    if (options.model === 'IMAGE') {{
                        return 'Image of: ' + filename; // prepend a label to all images by default
                    }}

                    filenameParts = filename.split('.');
                    filenameParts.pop(); // remove the last element (file extension)
                    return filenameParts.join('');
                }}

                // override the title util with this custom one
                window.wagtail.utils.getTitleFromFilename = getTitleFromFilename;
            }});
        </script>
        """
      )

