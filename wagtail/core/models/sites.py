from warnings import warn

from wagtail.models.sites import Site, SiteManager, SiteRootPath  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.models.sites is deprecated. "
    "Use wagtail.models.sites instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
