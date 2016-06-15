from __future__ import absolute_import, unicode_literals

import warnings

from wagtail.utils.deprecation import RemovedInWagtail17Warning
from wagtail.wagtailimages.views.serve import generate_signature, verify_signature  # noqa

warnings.warn(
    "The 'generate_signature' and 'verify_signature' functions have been moved. "
    "Please import them from the 'wagtail.wagtailimages.views.serve' module instead.",
    RemovedInWagtail17Warning)
