from collections import OrderedDict

from django.contrib.admin.utils import quote
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy

from wagtail.admin.ui.tables import BaseColumn, BulkActionsCheckboxColumn


class OrderingColumn(BaseColumn):
    header_template_name = "wagtailadmin/tables/ordering_header.html"
    cell_template_name = "wagtailadmin/tables/ordering_cell.html"


class OrderableTableMixin:
    success_message = gettext_lazy("'%(page_title)s' has been moved successfully.")

    def __init__(self, *args, sort_order_field=None, reorder_url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sort_order_field = sort_order_field
        self.reorder_url = reorder_url
        if self.reorder_url:
            self._add_ordering_column()

    @cached_property
    def ordering_column(self):
        return OrderingColumn("ordering", width="80px", sort_key=self.sort_order_field)

    def _add_ordering_column(self):
        self.columns = OrderedDict(
            [(self.ordering_column.name, self.ordering_column)]
            + [
                (column_name, column)
                for column_name, column in self.columns.items()
                # Replace bulk actions column with the ordering column if it exists
                if not isinstance(column, BulkActionsCheckboxColumn)
            ]
        )

    @property
    def attrs(self):
        attrs = super().attrs
        if self.reorder_url:
            attrs = {
                **attrs,
                "data-controller": "w-orderable",
                "data-w-orderable-active-class": "w-orderable--active",
                "data-w-orderable-chosen-class": "w-orderable__item--active",
                "data-w-orderable-container-value": "tbody",
                "data-w-orderable-message-value": self.get_success_message(),
                "data-w-orderable-url-value": self.reorder_url,
            }
        return attrs

    def get_success_message(self):
        return self.success_message % {"page_title": "__LABEL__"}

    def get_row_attrs(self, instance):
        attrs = super().get_row_attrs(instance)
        if self.reorder_url:
            attrs["id"] = "item_%s" % quote(instance.pk)
            attrs["data-w-orderable-item-id"] = quote(instance.pk)
            attrs["data-w-orderable-item-label"] = str(instance)
            attrs["data-w-orderable-target"] = "item"
        return attrs

    def get_caption(self):
        caption = super().get_caption()
        if not caption and self.reorder_url:
            return gettext(
                "Focus on the drag button and press up or down arrows to move the item, then press enter to submit the change."
            )
        return caption
