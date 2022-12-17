from warnings import warn

from wagtail.models.copying import (  # noqa
    _copy,
    _copy_m2m_relations,
    _extract_field_data,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.models.copying is deprecated. "
    "Use wagtail.models.copying instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
