.. _image_feature_detection:

Feature Detection
=================

Wagtail has the ability to automatically detect faces and features inside your images and crop the images to those features.

Feature detection uses third-party tools to detect faces/features in an image when the image is uploaded. The detected features stored internally as a focal point in the ``focal_point_{x, y, width, height}`` fields on the ``Image`` model. These fields are used by the ``fill`` image filter when an image is rendered in a template to crop the image.


Installation
------------

Two third-party tools are known to work with Wagtail: One based on OpenCV_ for general feature detection and one based on Rustface_ for face detection.

.. _OpenCV: https://opencv.org/

.. _Rustface: https://github.com/torchbox/rustface-py/

OpenCV on Debian/Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~

Feature detection requires OpenCV_ which can be a bit tricky to install as it's not currently pip-installable.

Debian and ubuntu provide an apt-get package called ``python-opencv``:

 .. code-block:: console

    $ sudo apt-get install python-opencv python-numpy

This will install PyOpenCV into your site packages. If you are using a virtual environment, you need to make sure site packages are enabled or Wagtail will not be able to import PyOpenCV.


Enabling site packages in the virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are not using a virtual environment, you can skip this step.

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


Rustface
~~~~~~~~

Rustface_ is python library with prebuilt wheel files provided for Linux and macOS. Although implemented in Rust it is pip-installable:

 .. code-block:: console

    $ pip install wheel
    $ pip install rustface


Registering with Willow
^^^^^^^^^^^^^^^^^^^^^^^

Rustface provides a plug-in that needs to be registered with Willow_.

This should be done somewhere that gets run on application startup:

 .. code-block:: python

    from willow.registry import registry
    import rustface.willow

    registry.register_plugin(rustface.willow)

For example, in an app's AppConfig.onready_.

.. _Willow: https://github.com/wagtail/Willow

.. _AppConfig.onready: https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready


Cropping
^^^^^^^^

The face detection algorithm produces a focal area that is tightly cropped to the face rather than the whole head.

For images with a single face this can be okay in some cases, e.g. thumbnails, it might be overly tight for "headshots".
Image renditions can encompass more of the head by reducing the crop percentage (``-c<percentage>``), at the end of the resize-rule, down to as low as 0%:

.. code-block:: html+django

    {% image page.photo fill-200x200-c0 %}


Switching on feature detection in Wagtail
-----------------------------------------

Once OpenCV is installed, you need to set the ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` setting to ``True``:

 .. code-block:: python

    # settings.py

    WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True


Manually running feature detection
----------------------------------

Feature detection runs when new images are uploaded in to Wagtail. If you already have images in your Wagtail site and would like to run feature detection on them, you will have to run it manually.

You can manually run feature detection on all images by running the following code in the python shell:

 .. code-block:: python

    from wagtail.images import get_image_model

    Image = get_image_model()

    for image in Image.objects.all():
        if not image.has_focal_point():
            image.set_focal_point(image.get_suggested_focal_point())
            image.save()