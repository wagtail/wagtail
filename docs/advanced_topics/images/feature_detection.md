(image_feature_detection)=

# Feature Detection

Wagtail has the ability to automatically detect faces and features inside your images and crop the images to those features.

Feature detection uses third-party tools to detect faces/features in an image when the image is uploaded. The detected features are stored internally as a focal point in the `focal_point_{x, y, width, height}` fields on the `Image` model. These fields are used by the `fill` image filter when an image is rendered in a template to crop the image.

## Installation

Two third-party tools are known to work with Wagtail: One based on [OpenCV](https://opencv.org/) for general feature detection and one based on [Rustface](https://github.com/torchbox/rustface-py/) for face detection.

### OpenCV on Debian/Ubuntu

Feature detection requires [OpenCV](https://opencv.org/) which can be a bit tricky to install as it's not currently pip-installable.

There is more than one way to install these components, but in each case you will need to test that both OpenCV itself _and_ the Python interface have been correctly installed.

#### Install `opencv-python`

[opencv-python](https://pypi.org/project/opencv-python/) is available on PyPI.
It includes a Python interface to OpenCV, as well as the statically-built OpenCV binaries themselves.

To install:

```console
$ pip install opencv-python
```

Depending on what else is installed on your system, this may be all that is required. On lighter-weight Linux systems, you may need to identify and install missing system libraries (for example, a slim version of Debian Stretch requires `libsm6 libxrender1 libxext6` to be installed with `apt`).

#### Install a system-level package

A system-level package can take care of all of the required components. Check what is available for your operating system. For example, [python-opencv](https://packages.debian.org/stretch/python-opencv) is available for Debian; it installs OpenCV itself, and sets up Python bindings.

However, it may make incorrect assumptions about how you're using Python (for example, which version you're using) - test as described below.

#### Testing the installation

Test the installation:

```python
python3
>>> import cv2
```

An error such as:

```python
ImportError: libSM.so.6: cannot open shared object file: No such file or directory
```

indicates that a required system library (in this case `libsm6`) has not been installed.

On the other hand,

```python
ModuleNotFoundError: No module named 'cv2'
```

means that the Python components have not been set up correctly in your Python environment.

If you don't get an import error, installation has probably been successful.

### Rustface

[Rustface](https://github.com/torchbox/rustface-py/) is Python library with prebuilt wheel files provided for Linux and macOS. Although implemented in Rust it is pip-installable:

```console
$ pip install wheel
$ pip install rustface
```

#### Registering with Willow

Rustface provides a plug-in that needs to be registered with [Willow](https://github.com/wagtail/Willow).

This should be done somewhere that gets run on application startup:

```python
from willow.registry import registry
import rustface.willow

registry.register_plugin(rustface.willow)
```

For example, in an app's [AppConfig.ready](https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready).

## Cropping

The face detection algorithm produces a focal area that is tightly cropped to the face rather than the whole head.

For images with a single face this can be okay in some cases, e.g. thumbnails, it might be overly tight for "headshots".
Image renditions can encompass more of the head by reducing the crop percentage (`-c<percentage>`), at the end of the resize-rule, down to as low as 0%:

```html+django
{% image page.photo fill-200x200-c0 %}
```

## Switching on feature detection in Wagtail

Once installed, you need to set the `WAGTAILIMAGES_FEATURE_DETECTION_ENABLED` setting to `True` to automatically detect faces/features whenever a new image is uploaded in to Wagtail or when an image without a focal point is saved (this is done via a pre-save signal handler):

```python
# settings.py

WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True
```

## Manually running feature detection

If you already have images in your Wagtail site and would like to run feature detection on them, or you want to apply feature detection selectively when the `WAGTAILIMAGES_FEATURE_DETECTION_ENABLED` is set to `False` you can run it manually using the `get_suggested_focal_point()` method on the `Image` model.

For example, you can manually run feature detection on all images by running the following code in the python shell:

```python
from wagtail.images import get_image_model

Image = get_image_model()

for image in Image.objects.all():
    if not image.has_focal_point():
        image.set_focal_point(image.get_suggested_focal_point())
        image.save()
```
