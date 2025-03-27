from collections import namedtuple

import django_filters
from django.core.exceptions import ImproperlyConfigured
from django.forms import BoundField, ModelChoiceField
from django.http import QueryDict
from django.utils.formats import date_format

from wagtail.utils.registry import ObjectTypeRegistry
from wagtail.utils.utils import flatten_choices

# Represents a django-filter filter that is currently in force on a listing queryset
ActiveFilter = namedtuple(
    "ActiveFilter", ["auto_id", "field_label", "value", "removed_filter_url"]
)


class BaseFilterAdapter:
    def __init__(
        self,
        filter: django_filters.Filter,
        bound_field: BoundField,
        value,
        base_url: str,
        query_dict: QueryDict,
    ):
        self.filter = filter
        self.bound_field = bound_field
        self.value = value
        self.base_url = base_url
        self.query_dict = query_dict

    def get_url_without_filter_param(self, param):
        """
        Return the base URL with the given filter parameter removed from the
        query string.
        """
        query_dict = self.query_dict.copy()
        if isinstance(param, (list, tuple)):
            for p in param:
                query_dict.pop(p, None)
        else:
            query_dict.pop(param, None)
        return self.base_url + "?" + query_dict.urlencode()

    def get_url_without_filter_param_value(self, param, value):
        """
        Return the index URL where the filter parameter with the given value has
        been removed from the query string, preserving all other values for that
        parameter.
        """
        query_dict = self.query_dict.copy()
        query_dict.setlist(
            param, [v for v in query_dict.getlist(param) if v != str(value)]
        )
        return self.base_url + "?" + query_dict.urlencode()

    def get_active_filters(self):
        """
        Return a list of `ActiveFilter` objects representing the filter values
        that are currently in force on the listing queryset.
        """
        yield ActiveFilter(
            self.bound_field.auto_id,
            self.filter.label,
            str(self.value),
            self.get_url_without_filter_param(self.bound_field.name),
        )


class ChoiceFilterAdapter(BaseFilterAdapter):
    def get_active_filters(self):
        choices = flatten_choices(self.filter.field.choices)
        yield (
            ActiveFilter(
                self.bound_field.auto_id,
                self.filter.label,
                choices.get(str(self.value), str(self.value)),
                self.get_url_without_filter_param(self.bound_field.name),
            )
        )


class MultipleChoiceFilterAdapter(BaseFilterAdapter):
    def get_active_filters(self):
        choices = flatten_choices(self.filter.field.choices)
        yield from (
            ActiveFilter(
                self.bound_field.auto_id,
                self.filter.label,
                choices.get(str(item), str(item)),
                self.get_url_without_filter_param_value(self.bound_field.name, item),
            )
            for item in self.value
        )


class ModelChoiceFilterAdapter(BaseFilterAdapter):
    def get_active_filters(self):
        field: ModelChoiceField = self.filter.field
        yield (
            ActiveFilter(
                self.bound_field.auto_id,
                self.filter.label,
                field.label_from_instance(self.value),
                self.get_url_without_filter_param(self.bound_field.name),
            )
        )


class ModelMultipleChoiceFilterAdapter(BaseFilterAdapter):
    def get_active_filters(self):
        field: ModelChoiceField = self.filter.field
        yield from (
            ActiveFilter(
                self.bound_field.auto_id,
                self.filter.label,
                field.label_from_instance(item),
                self.get_url_without_filter_param_value(self.bound_field.name, item.pk),
            )
            for item in self.value
        )


class DateFromToRangeFilterAdapter(BaseFilterAdapter):
    def get_active_filters(self):
        start_date_display = date_format(self.value.start) if self.value.start else ""
        end_date_display = date_format(self.value.stop) if self.value.stop else ""
        widget = self.filter.field.widget
        yield (
            ActiveFilter(
                self.bound_field.auto_id,
                self.filter.label,
                f"{start_date_display} - {end_date_display}",
                self.get_url_without_filter_param(
                    [
                        widget.suffixed(self.bound_field.name, suffix)
                        for suffix in widget.suffixes
                    ]
                ),
            )
        )


filter_adapter_class_registry = ObjectTypeRegistry()


def register_filter_adapter_class(
    filter_class: django_filters.Filter,
    adapter_class: BaseFilterAdapter = None,
    exact_class: BaseFilterAdapter = False,
):
    """
    Define how a django-filter Filter should be displayed when it's active.
    The ``adapter_class`` should be a subclass of
    ``wagtail.admin.active_filters.BaseFilterAdapter``.

    This is mainly useful for defining how active filters are rendered in
    listing views.
    """
    if adapter_class is None:
        raise ImproperlyConfigured(
            "register_filter_adapter_class must be passed a 'adapter_class' keyword argument"
        )

    filter_adapter_class_registry.register(
        filter_class,
        value=adapter_class,
        exact_class=exact_class,
    )


register_filter_adapter_class(
    django_filters.Filter,
    BaseFilterAdapter,
)
register_filter_adapter_class(
    django_filters.ChoiceFilter,
    ChoiceFilterAdapter,
)
register_filter_adapter_class(
    django_filters.MultipleChoiceFilter,
    MultipleChoiceFilterAdapter,
)
register_filter_adapter_class(
    django_filters.ModelChoiceFilter,
    ModelChoiceFilterAdapter,
)
register_filter_adapter_class(
    django_filters.ModelMultipleChoiceFilter,
    ModelMultipleChoiceFilterAdapter,
)
register_filter_adapter_class(
    django_filters.DateFromToRangeFilter,
    DateFromToRangeFilterAdapter,
)
