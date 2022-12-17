from warnings import warn

from wagtail.models.collections import (  # noqa
    BaseCollectionManager,
    Collection,
    CollectionManager,
    CollectionMember,
    CollectionViewRestriction,
    GroupCollectionPermission,
    GroupCollectionPermissionManager,
    get_root_collection_id,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.models.collections is deprecated. "
    "Use wagtail.models.collections instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
