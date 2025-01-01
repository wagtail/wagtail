from django.contrib.contenttypes.models import ContentType

from wagtail.coreutils import resolve_model_string


class ContentTypeOrder:
    def __init__(self):
        self.model_order = {}
        self.content_type_order = {}
        self.valid = False

    def register(self, model, **kwargs):
        """
        Registers order against the model content_type, used to
        control the order the models and its permissions appear
        in the groups object permission editor
        """
        order = kwargs.pop("order", None)
        if order is not None:
            self.model_order[resolve_model_string(model)] = order
            self.valid = False

    def get(self, content_type, default=None):
        if not self.valid:
            self.content_type_order = {
                ContentType.objects.get_for_model(model).id: order
                for model, order in self.model_order.items()
            }
            self.valid = True

        return self.content_type_order.get(content_type, default)


content_type_order = ContentTypeOrder()


def register(model, **kwargs):
    content_type_order.register(model, **kwargs)
