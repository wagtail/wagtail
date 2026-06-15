from wagtail.documents import get_document_model_string
from wagtail.permissions import get_permission_policy, collection_ownership_permission_policy_class

permission_policy = get_permission_policy("document", default=collection_ownership_permission_policy_class)(
    get_document_model_string(),
    auth_model="wagtaildocs.Document",
    owner_field_name="uploaded_by_user",
)