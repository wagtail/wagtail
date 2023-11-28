from django.test.signals import setting_changed

from wagtail.documents import get_document_model, get_permission_policy
from wagtail.permissions import policies_registry as policies


def update_permission_policy(signal, sender, setting, **kwargs):
    """
    Register the permission policy when the `WAGTAILDOCS_DOCUMENT_MODEL` setting changes.
    This is useful in tests where we override the document model setting and expect the
    permission policy to have changed accordingly.
    """

    if setting == "WAGTAILDOCS_DOCUMENT_MODEL":
        policies.register(get_document_model(), get_permission_policy())


setting_changed.connect(update_permission_policy)
