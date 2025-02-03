from django.contrib.contenttypes.models import ContentType

from wagtail.coreutils import resolve_model_string

content_types_to_register = []
CONTENT_TYPE_ORDER = {}


def register(model, **kwargs):
    """
    Registers order against the model content_type, used to
    control the order the models and its permissions appear
    in the groups object permission editor
    """
    order = kwargs.pop("order", None)
    if order is not None:
        # We typically call this at application startup, when the database may not be ready,
        # and so we can't look up the content type yet. Instead we will queue up the
        # (model, order) pair to be processed when the lookup is requested.
        content_types_to_register.append((model, order))


def get_content_type_order_lookup():
    if content_types_to_register:
        for model, order in content_types_to_register:
            content_type = ContentType.objects.get_for_model(
                resolve_model_string(model)
            )
            CONTENT_TYPE_ORDER[content_type.id] = order
        content_types_to_register.clear()
    return CONTENT_TYPE_ORDER
