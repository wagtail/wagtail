from django.test.signals import setting_changed

from wagtail.images import get_image_model, get_permission_policy
from wagtail.permissions import policies_registry as policies


def update_permission_policy(signal, sender, setting, **kwargs):
    """
    Register the permission policy when the `WAGTAILIMAGES_IMAGE_MODEL` setting changes.
    This is useful in tests where we override the image model setting and expect the
    permission policy to have changed accordingly.
    """

    if setting == "WAGTAILIMAGES_IMAGE_MODEL":
        policies.register(get_image_model(), get_permission_policy())


setting_changed.connect(update_permission_policy)
