import warnings

from wagtail.blocks import *  # noqa: F403

warnings.warn(
    "wagtail.admin.blocks has moved to wagtail.blocks", UserWarning, stacklevel=2
)
