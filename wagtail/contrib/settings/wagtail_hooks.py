from django.urls import include, path

from wagtail.core import hooks
from . import urls


@hooks.register("get_avatar_url")
def custom_avatar_url(user, size):
    if "fred" in user.username:
        return f"https://example.com/avatars/fred-{size}.png"
    return None
