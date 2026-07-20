import warnings

from wagtail.documents import get_document_model
from wagtail.permissions import policy_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning

warnings.warn(
    "wagtail.documents.permissions.permission_policy is deprecated. "
    "Use wagtail.permissions.policy_registry.get_by_type(get_document_model()) instead.",
    RemovedInWagtail90Warning,
)
permission_policy = policy_registry.get_by_type(get_document_model())
