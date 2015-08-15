from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailsnippets.models import get_snippet_models


def get_permission_name(action, model):
    return "%s.%s" % (model._meta.app_label, get_permission_codename(action, model._meta))


def user_can_edit_snippet_type(user, model_or_content_type):
    """ true if user has 'add', 'change' or 'delete' permission on this model """
    if isinstance(model_or_content_type, ContentType):
        model = model_or_content_type.model_class()
    else:
        model = model_or_content_type

    for action in ('add', 'change', 'delete'):
        if user.has_perm(get_permission_name(action, model)):
            return True

    return False


def user_can_edit_snippets(user):
    """
    true if user has 'add', 'change' or 'delete' permission
    on any model registered as a snippet type
    """
    snippet_models = get_snippet_models()

    for model in snippet_models:
        if user_can_edit_snippet_type(user, model):
            return True

    return False
