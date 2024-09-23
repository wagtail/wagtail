from functools import lru_cache

from django.contrib.contenttypes.models import ContentType

from wagtail import hooks
from wagtail.coreutils import safe_snake_case
from wagtail.models import get_page_models
from wagtail.permissions import page_permission_policy


def get_field_clean_name(label):
    """
    Converts a user entered field label to a string that is safe to use for both a
    HTML attribute (field's name) and a JSON key used internally to store the responses.
    """
    return safe_snake_case(label)


@lru_cache(maxsize=None)
def get_form_types():
    from wagtail.contrib.forms.models import FormMixin

    form_models = [model for model in get_page_models() if issubclass(model, FormMixin)]

    return list(ContentType.objects.get_for_models(*form_models).values())


def get_forms_for_user(user):
    """
    Return a queryset of form pages that this user is allowed to access the submissions for
    """
    editable_forms = page_permission_policy.instances_user_has_permission_for(
        user, "change"
    )
    editable_forms = editable_forms.filter(content_type__in=get_form_types())

    # Apply hooks
    for fn in hooks.get_hooks("filter_form_submissions_for_user"):
        editable_forms = fn(user, editable_forms)

    return editable_forms
