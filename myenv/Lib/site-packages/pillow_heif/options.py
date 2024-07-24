"""Options to change pillow_heif's runtime behavior."""

DECODE_THREADS = 4
"""Maximum number of threads to use for decoding images(when it is possible)

When use pillow_heif as a plugin you can set it with: `register_*_opener(decode_threads=8)`"""


THUMBNAILS = True
"""Option to enable/disable thumbnail support

When use pillow_heif as a plugin you can set it with: `register_*_opener(thumbnails=False)`"""


DEPTH_IMAGES = True
"""Option to enable/disable depth image support

When use pillow_heif as a plugin you can set it with: `register_*_opener(depth_images=False)`"""


QUALITY = None
"""Default encoding quality

.. note:: Quality specified during calling ``save`` has higher priority then this.

Possible values: None, -1, range(0-100).
Set -1 for lossless quality or from 0 to 100, where 0 is lowest and 100 is highest.

.. note:: Also for lossless encoding you should specify ``chroma=444`` during save.

When use pillow_heif as a plugin you can set it with: `register_*_opener(quality=-1)`"""


SAVE_HDR_TO_12_BIT = False
"""Should 16 bit images be saved to 12 bit instead of 10 bit``

When use pillow_heif as a plugin you can set it with: `register_*_opener(save_to_12bit=True)`"""


ALLOW_INCORRECT_HEADERS = False
"""Can or not the ``size`` of image in header differ from decoded one.

.. note:: If enabled, ``Image.size`` can change after loading for images where it is invalid in header.

To learn more read: `here <https://github.com/strukturag/libheif/issues/784>`_

When use pillow_heif as a plugin you can set it with: `register_*_opener(allow_incorrect_headers=True)`"""


SAVE_NCLX_PROFILE = True
"""Should be ``nclx`` profile saved or not.

Default for all previous versions(pillow_heif<0.14.0) was NOT TO save `nclx` profile,
due to an old bug in Apple software refusing to open images with `nclx` profiles.
Apple has already fixed this and there is no longer a need to not save the default profile.

.. note:: `save_nclx_profile` specified during calling ``save`` has higher priority than this.

When use pillow_heif as a plugin you can unset it with: `register_*_opener(save_nclx_profile=False)`"""


PREFERRED_ENCODER = {
    "AVIF": "",
    "HEIF": "",
}
"""Use the specified encoder for format.

You can get the available encoders IDs using ``libheif_info()`` function.

When use pillow_heif as a plugin you can set this option with ``preferred_encoder`` key.

.. note:: If the specified encoder is missing, the option will be ignored."""


PREFERRED_DECODER = {
    "AVIF": "",
    "HEIF": "",
}
"""Use the specified decoder for format.

You can get the available decoders IDs using ``libheif_info()`` function.

When use pillow_heif as a plugin you can set this option with ``preferred_decoder`` key.

.. note:: If the specified decoder is missing, the option will be ignored."""
