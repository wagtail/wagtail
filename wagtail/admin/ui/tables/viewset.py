from django.contrib.admin.utils import quote
from django.utils.translation import gettext

from wagtail.admin.ui.tables import Table


class ViewSetModelTable(Table):
    def __init__(self, *args, use_ordering_attributes=False, **kwargs):
        super().__init__(*args, **kwargs)

        # If true, extra attributes will be added for the stimulus controller.
        self.use_ordering_attributes = use_ordering_attributes

    @property
    def attrs(self):
        attrs = super().attrs
        if self.use_ordering_attributes:
            attrs = {
                **attrs,
                "data-controller": "w-orderable",
                "data-w-orderable-active-class": "w-orderable--active",
                "data-w-orderable-chosen-class": "w-orderable__item--active",
                "data-w-orderable-container-value": "tbody",
                "data-w-orderable-message-value": gettext(
                    "Item has been moved successfully."
                ),
                "data-w-orderable-url-value": self.base_url + "reorder/999999/",
            }
        return attrs

    def get_row_attrs(self, instance):
        attrs = super().get_row_attrs(instance)
        if self.use_ordering_attributes:
            attrs["id"] = "item_%s" % quote(instance.pk)
            attrs["data-w-orderable-item-id"] = quote(instance.pk)
            attrs["data-w-orderable-item-label"] = str(instance)
            attrs["data-w-orderable-target"] = "item"
        return attrs
