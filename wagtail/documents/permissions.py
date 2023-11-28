from wagtail.documents import get_document_model
from wagtail.permissions import policies_registry as policies

# This is deprecated, but kept for backwards compatibility
# The policy should be retrieved using `policies.get_by_type(get_document_model())`
# TODO: Add deprecation warning
permission_policy = policies.get_by_type(get_document_model())
