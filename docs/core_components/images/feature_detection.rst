=================
Feature Detection
=================

Wagtail has the ability to automatically detect faces and features inside your images and automatically crop the images to those features.

Feature detection is used by the ``fill`` image filter. An image that has had feature detection run on it would be cropped based on the features that were detected.


Setup
=====

Feature detection requires OpenCV which can be a bit tricky to set up as it is not currently pip-installable.


Installing OpenCV on Debian/Ubuntu
----------------------------------

Debian and ubuntu provide ``python-opencv`` as a package installable with apt-get:

 .. code-block:: bash

    sudo apt-get install python-opencv python-numpy


If you are using a Virtual environment, you will need to make sure that you have site packages enabled so python can see OpenCV.

For Python 3, go into your pyvenv directory and open the ``pyvenv.cfg`` file then set ``include-system-site-packages`` to ``true``.

If you are using Virtualenv, go into your virtualenv directory and delete a file called ``lib/python-x.x/no-global-site-packages.txt``.


You can test that it's all working by opening up a python shell (with your virtual environment active) and typing:

 .. code-block:: python

    import cv

If you don't see an ``ImportError``, it worked.


Switching on feature detection
------------------------------

Once OpenCV is installed, you need to switch on feature detection in Wagtail

You can do this by seting the ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` setting to ``True``:

 .. code-block:: python

    # settings.py

    WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True


Feature detection runs when new images are uploaded in to Wagtail. If you already have images in your Wagtail site and would like to run feature detection on them, you will have to run it manually.


Manually running feature detection
----------------------------------

You can manually feature detection on all images by running the following code in the python shell:

 .. code-block:: python

    from wagtail.wagtailimages.models import Image

    for image in Image.objects.all():
        if image.focal_point is None:
            image.focal_point = image.get_suggested_focal_point()
            image.save()
