from django.contrib.contenttypes.models import ContentType

from wagtail import hooks
from wagtail.coreutils import safe_snake_case
from wagtail.models import UserPagePermissionsProxy, get_page_models

_FORM_CONTENT_TYPES = None


def get_field_clean_name(label):
    """
    Converts a user entered field label to a string that is safe to use for both a
    HTML attribute (field's name) and a JSON key used internally to store the responses.
    """
    return safe_snake_case(label)


def get_form_types():
    global _FORM_CONTENT_TYPES
    if _FORM_CONTENT_TYPES is None:
        from wagtail.contrib.forms.models import AbstractForm

        form_models = [
            model for model in get_page_models() if issubclass(model, AbstractForm)
        ]

        _FORM_CONTENT_TYPES = list(
            ContentType.objects.get_for_models(*form_models).values()
        )
    return _FORM_CONTENT_TYPES


def get_forms_for_user(user):
    """
    Return a queryset of form pages that this user is allowed to access the submissions for
    """
    editable_forms = UserPagePermissionsProxy(user).editable_pages()
    editable_forms = editable_forms.filter(content_type__in=get_form_types())

    # Apply hooks
    for fn in hooks.get_hooks("filter_form_submissions_for_user"):
        editable_forms = fn(user, editable_forms)

    return editable_forms
