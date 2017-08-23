.. _image_feature_detection:

Feature Detection
=================

Wagtail has the ability to automatically detect faces and features inside your images and crop the images to those features.

Feature detection uses OpenCV to detect faces/features in an image when the image is uploaded. The detected features stored internally as a focal point in the ``focal_point_{x, y, width, height}`` fields on the ``Image`` model. These fields are used by the ``fill`` image filter when an image is rendered in a template to crop the image.


Setup
-----

Feature detection requires OpenCV which can be a bit tricky to install as it's not currently pip-installable.


Installing OpenCV on Debian/Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Debian and ubuntu provide an apt-get package called ``python-opencv``:

 .. code-block:: console

    $ sudo apt-get install python-opencv python-numpy

This will install PyOpenCV into your site packages. If you are using a virtual environment, you need to make sure site packages are enabled or Wagtail will not be able to import PyOpenCV.


Enabling site packages in the virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are not using a virtual envionment, you can skip this step.

Enabling site packages is different depending on whether you are using pyvenv (Python 3.3+ only) or virtualenv to manage your virtual environment.


pyvenv
``````

Go into your pyvenv directory and open the ``pyvenv.cfg`` file then set ``include-system-site-packages`` to ``true``.


virtualenv
``````````

Go into your virtualenv directory and delete a file called ``lib/python-x.x/no-global-site-packages.txt``.


Testing the OpenCV installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can test that OpenCV can be seen by Wagtail by opening up a python shell (with your virtual environment active) and typing:

 .. code-block:: python

    import cv

If you don't see an ``ImportError``, it worked. (If you see the error ``libdc1394 error: Failed to initialize libdc1394``, this is harmless and can be ignored.)


Switching on feature detection in Wagtail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once OpenCV is installed, you need to set the ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` setting to ``True``:

 .. code-block:: python

    # settings.py

    WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True


Manually running feature detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Feature detection runs when new images are uploaded in to Wagtail. If you already have images in your Wagtail site and would like to run feature detection on them, you will have to run it manually.

You can manually run feature detection on all images by running the following code in the python shell:

 .. code-block:: python

    from wagtail.wagtailimages.models import Image

    for image in Image.objects.all():
        if not image.has_focal_point():
            image.set_focal_point(image.get_suggested_focal_point())
            image.save()
