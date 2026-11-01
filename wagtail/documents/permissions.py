import warnings

from wagtail.documents import get_document_model, get_permission_policy
from wagtail.permissions import policy_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning

warnings.warn(
    "wagtail.documents.permissions.permission_policy is deprecated. "
    "Use wagtail.permissions.policy_registry.get_by_type(get_document_model()) instead.",
    RemovedInWagtail90Warning,
    stacklevel=2,
)
# Do not use a fallback here, as it would prevent the real permission policy
# from being registered if there is code that imports this module before the
# app's ready() is called.
permission_policy = policy_registry.get_by_type(get_document_model(), fallback=False)
if not permission_policy:
    permission_policy = get_permission_policy()
    warnings.warn(
        "wagtail.documents.permissions was imported before wagtail.documents app is "
        "ready. Avoid importing wagtail.documents.permissions at the module level.",
        RuntimeWarning,
        stacklevel=2,
    )
