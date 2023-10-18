from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from wagtail.models import get_page_models


def get_content_types_for_filter():
    models = [model.__name__.lower() for model in get_page_models()]
    return ContentType.objects.filter(model__in=models).order_by("model")


def get_users_for_filter():
    User = get_user_model()
    return User.objects.filter(locked_pages__isnull=False).order_by(User.USERNAME_FIELD)
