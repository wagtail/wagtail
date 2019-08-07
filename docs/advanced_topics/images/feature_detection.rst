.. _image_feature_detection:

Feature Detection
=================

Wagtail has the ability to automatically detect faces and features inside your images and crop the images to those features.

Feature detection uses `OpenCV <https://opencv.org>`_, the Open Source Computer Vision Library, to detect faces/features in an image when the image is uploaded. The detected features are stored internally as a focal point in the ``focal_point_{x, y, width, height}`` fields on the ``Image`` model. These fields are used by the ``fill`` image filter when an image is rendered in a template to crop the image.


Installation
------------

Three components are required to get this working with Wagtail:

* OpenCV itself
* various system-level components that OpenCV relies on
* a Python interface to OpenCV, exposed as ``cv2``


Installation options
~~~~~~~~~~~~~~~~~~~~

There is more than one way to install these components, but in each case you will need to test that both OpenCV itself *and* the Python interface have been correctly installed.


Install ``opencv-python``
`````````````````````````

`opencv-python <https://pypi.org/project/opencv-python/>`_ is available on PyPI.
It includes a Python interface to OpenCV, as well as the statically-built OpenCV binaries themselves.

To install:

.. code-block:: console

    $ pip install opencv-python

Depending on what else is installed on your system, this may be all that is required. On lighter-weight Linux systems, you may need to identify and install missing system libraries (for example, a slim version of Debian Stretch requires ``libsm6 libxrender1 libxext6`` to be installed with ``apt``).


Install a system-level package
``````````````````````````````

A system-level package can take care of all of the required components. Check what is available for your operating system. For example, `python-opencv <https://packages.debian.org/stretch/python-opencv>`_ is available for Debian; it installs OpenCV itself, and sets up Python bindings.

However, it may make incorrect assumptions about how you're using Python (for example, which version you're using) - test as described below.


Testing the installation
````````````````````````

Test the installation::

    python3
    >>> import cv2

An error such as::

    ImportError: libSM.so.6: cannot open shared object file: No such file or directory

indicates that a required system library (in this case ``libsm6``) has not been installed.

On the other hand,

::

    ModuleNotFoundError: No module named 'cv2'

means that the Python components have not been set up correctly in your Python environment.

If you don't get an import error, installation has probably been successful.


Switching on feature detection in Wagtail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once OpenCV is installed, you need to set the ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` setting to ``True``:

 .. code-block:: python

    # settings.py

    WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True


Manually running feature detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Feature detection runs when new images are uploaded in to Wagtail. If you already have images in your Wagtail site and would like to run feature detection on them, you will have to run it manually.

You can manually run feature detection on all images by running the following code in the Python shell:

 .. code-block:: python

    from wagtail.images.models import Image

    for image in Image.objects.all():
        if not image.has_focal_point():
            image.set_focal_point(image.get_suggested_focal_point())
            image.save()
