.. _image_custom_title_generation_from_filename:

Custom Title Generation From Filename
=====================================

Override how the title is set when uploading single files, multiple files or uploading a file within a chooser modal.

.. note::
    This will not apply to editing images (e.g. uploading a replacement image file while editing an existing image).

``wagtail.utils.getImageUploadTitle`` can be overridden with a custom function,
the first argument is the filename (e.g. ``'some_file.jpg'``) and the second is an options object.
If the return value is a ``String`` it will replace the value in the relevant title field, otherwise it will leave the title field as is (blank).

The options available to the function are as follows:

* ``event`` - event triggered by the DOM element
* ``maxLength`` - will be the maximum length on the title form field (may not available for some forms, can be null)
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
                function getImageUploadTitle (filename, options) {{
                    filenameParts = filename.split('.');
                    filenameParts.pop(); // remove the last element (file extension)
                    return ['IMAGE - '].concat(filenameParts).join(''); // return the desired title to be used
                }}
                window.wagtail.utils.getImageUploadTitle = getImageUploadTitle;
            }});
        </script>
        """
      )

