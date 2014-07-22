=======================
Image Feature Detection
=======================

Wagtail has the ability to automatically detect faces and features inside your images and automatically crop the images to those features.

Feature detection is used by the ``fill`` image filter. An image that has had feature detection run on it would be cropped based on the features that were detected.


Setup
=====

Feature detection requires OpenCV which can be a bit tricky to set up as it is not currently pip-installable.


Installing OpenCV on Debian/Ubuntu
----------------------------------

Debian and ubuntu provide python-opencv as a package installable with apt-get:

 .. code-block:: bash

    sudo apt-get install python-opencv python-numpy


If you are using a Virtual environment, you will need to make sure that you have site packages enabled.

For Python 3, go into your virtualenv directory and open the ``pyvenv.cfg`` file then set ``include-system-site-packages`` to ``true``.

If you are using Virtualenv, go into your virtualenv directory and delete a file called ``lib/python-x.x/no-global-site-packages.txt``.


You can test that its all working by opening up a python shell (with your virtual environment active) and typing:

 .. code-block:: python

    import cv


Switching on feature detection
------------------------------

To switch on feature detection, set the ``WAGTAIL_FEATURE_DETECTION_ENABLED`` setting to ``True``:

 .. code-block:: python

    # settings.py

    WAGTAIL_FEATURE_DETECTION_ENABLED = True


Feature detection runs when images are uploaded so any images you already have will behave as they used to.

If you have images in your site that you want to have 