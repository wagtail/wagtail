.. _Upload to:

Handling uploaded files with a model
=====================================

Model forms perform validation, automatically builds the absolute path for the upload, treats filename conflicts and other common tasks.


See the example below:

.. code-block:: python

    document = models.FileField(upload_to='documents/')

Note the upload_to parameter. The files will be automatically uploaded to ``MEDIA_ROOT/documents/.``

It is also possible to do something like:

.. code-block:: python

    document = models.FileField(upload_to='documents/%Y/%m/%d/')

A file uploaded today would be uploaded to ``MEDIA_ROOT/documents/2016/08/01/.``

The ``upload_to`` can also be a callable that returns a string. This callable accepts two parameters, instance and filename.


.. code-block:: python

    def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)

    class MyModel(models.Model):
    upload = models.FileField(upload_to=user_directory_path)

If you’re saving a file on a Model with a FileField, using a ModelForm makes this process much easier. The file object will be saved to the location specified by the upload_to argument of the corresponding FileField when calling ``form.save():.`` 

in Your view.py

.. code-block:: python

    from django.http import HttpResponseRedirect
    from django.shortcuts import render
    from .forms import ModelFormWithFileField

    def upload_file(request):
    if request.method == 'POST':
        form = ModelFormWithFileField(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            form.save()
            return HttpResponseRedirect('/success/url/')
    else:
        form = ModelFormWithFileField()
    return render(request, 'upload.html', {'form': form})
