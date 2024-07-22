from django.contrib.contenttypes.models import ContentType

from wagtail import hooks
from wagtail.coreutils import safe_snake_case
from wagtail.models import get_page_models
from wagtail.permissions import page_permission_policy

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
        from wagtail.contrib.forms.models import FormMixin

        form_models = [
            model for model in get_page_models() if issubclass(model, FormMixin)
        ]

        _FORM_CONTENT_TYPES = list(
            ContentType.objects.get_for_models(*form_models).values()
        )
    return _FORM_CONTENT_TYPES


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

def get_form_submissions_as_data(
    data_fields={}, submissions=[], orderable_fields=[], ordering_by_field={}
):
    """
    Build data_rows as list of dicts containing id and fields and
    build data_headings as list of dicts containing id and fields
    """

    data_rows = []
    for submission in submissions:
        form_data = submission.get_data()
        data_row = []
        for name, label in data_fields:
            val = form_data.get(name)
            if isinstance(val, list):
                val = ", ".join(val)
            data_row.append(val)
        data_rows.append({"id": submission.id, "fields": data_row})

    data_headings = []
    for name, label in data_fields:
        order_label = None
        if name in orderable_fields:
            order = ordering_by_field.get(name)
            if order:
                order_label = order[1]  # 'ascending' or 'descending'
            else:
                order_label = "orderable"  # not ordered yet but can be
        data_headings.append(
            {
                "name": name,
                "label": label,
                "order": order_label,
            }
        )

    return (
        data_headings,
        data_rows,
    )