import django_filters
from django import forms
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_filters.widgets import SuffixedMultiWidget

from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.utils import get_user_display_name
from wagtail.admin.widgets import AdminDateInput, BooleanRadioSelect, FilteredSelect
from wagtail.coreutils import get_content_languages, get_content_type_label
from wagtail.models import Locale


class DateRangePickerWidget(SuffixedMultiWidget):
    """
    A widget allowing a start and end date to be picked.
    """

    template_name = "wagtailadmin/widgets/daterange_input.html"
    suffixes = ["from", "to"]

    def __init__(self, attrs=None):
        widgets = (
            AdminDateInput(attrs={"placeholder": _("Date from")}),
            AdminDateInput(attrs={"placeholder": _("Date to")}),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class FilteredModelChoiceIterator(django_filters.fields.ModelChoiceIterator):
    """
    A variant of Django's ModelChoiceIterator that, instead of yielding (value, label) tuples,
    returns (value, label, filter_value) so that FilteredSelect can drop filter_value into
    the data-filter-value attribute.
    """

    def choice(self, obj):
        return (
            self.field.prepare_value(obj),
            self.field.label_from_instance(obj),
            self.field.get_filter_value(obj),
        )


class FilteredModelChoiceField(django_filters.fields.ModelChoiceField):
    """
    A ModelChoiceField that uses FilteredSelect to dynamically show/hide options based on another
    ModelChoiceField of related objects; an option will be shown whenever the selected related
    object is present in the result of filter_accessor for that option.

    filter_field - the HTML `id` of the related ModelChoiceField
    filter_accessor - either the name of a relation, property or method on the model instance which
        returns a queryset of related objects, or a function which accepts the model instance and
        returns such a queryset.
    """

    widget = FilteredSelect
    iterator = FilteredModelChoiceIterator

    def __init__(self, *args, **kwargs):
        self.filter_accessor = kwargs.pop("filter_accessor")
        filter_field = kwargs.pop("filter_field")
        super().__init__(*args, **kwargs)
        self.widget.filter_field = filter_field

    def get_filter_value(self, obj):
        # Use filter_accessor to obtain a queryset of related objects
        if callable(self.filter_accessor):
            queryset = self.filter_accessor(obj)
        else:
            # treat filter_accessor as a method/property name of obj
            queryset = getattr(obj, self.filter_accessor)
            if isinstance(queryset, models.Manager):
                queryset = queryset.all()
            elif callable(queryset):
                queryset = queryset()

        # Turn this queryset into a list of IDs that will become the 'data-filter-value' used to
        # filter this listing
        return queryset.values_list("pk", flat=True)


class FilteredModelChoiceFilter(django_filters.ModelChoiceFilter):
    field_class = FilteredModelChoiceField


class LocaleFilter(django_filters.ChoiceFilter):
    def filter(self, qs, language_code):
        if language_code:
            try:
                locale_id = (
                    Locale.objects.filter(language_code=language_code)
                    .values_list("pk", flat=True)
                    .get()
                )
            except Locale.DoesNotExist:
                return qs.none()
            return qs.filter(locale_id=locale_id)
        return qs


class WagtailFilterSet(django_filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            self._add_locale_filter()

    def _add_locale_filter(self):
        # Add a locale filter if the model is translatable
        # and there isn't one already.
        from wagtail.models.i18n import Locale, TranslatableMixin

        if (
            self._meta.model
            and issubclass(self._meta.model, TranslatableMixin)
            and "locale" not in self.filters
        ):
            # Only add the locale filter if there are multiple content languages
            # in the settings and the corresponding Locales exist.
            languages = get_content_languages()
            locales = set(Locale.objects.values_list("language_code", flat=True))
            choices = [(k, v) for k, v in languages.items() if k in locales]
            if len(choices) <= 1:
                return

            self.filters["locale"] = LocaleFilter(
                label=_("Locale"),
                choices=choices,
                empty_label=None,
                null_label=_("All"),
                null_value=None,
                widget=forms.RadioSelect,
            )

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):
        filter_class, params = super().filter_for_lookup(field, lookup_type)

        if filter_class == django_filters.ChoiceFilter:
            params.setdefault("widget", forms.RadioSelect)
            params.setdefault("empty_label", _("All"))

        elif filter_class in [django_filters.DateFilter, django_filters.DateTimeFilter]:
            params.setdefault("widget", AdminDateInput)

        elif filter_class == django_filters.DateFromToRangeFilter:
            params.setdefault("widget", DateRangePickerWidget)

        elif filter_class == django_filters.BooleanFilter:
            params.setdefault("widget", BooleanRadioSelect)

        return filter_class, params


class ContentTypeModelChoiceField(django_filters.fields.ModelChoiceField):
    """
    Custom ModelChoiceField for ContentType, to show the model verbose name as the label rather
    than the default 'wagtailcore | page' representation of a ContentType
    """

    def label_from_instance(self, obj):
        return get_content_type_label(obj)


class ContentTypeFilter(django_filters.ModelChoiceFilter):
    field_class = ContentTypeModelChoiceField


class ContentTypeModelMultipleChoiceField(
    django_filters.fields.ModelMultipleChoiceField
):
    """
    Custom ModelMultipleChoiceField for ContentType, to show the model verbose name as the label rather
    than the default 'wagtailcore | page' representation of a ContentType
    """

    def label_from_instance(self, obj):
        return get_content_type_label(obj)


class MultipleContentTypeFilter(django_filters.ModelMultipleChoiceFilter):
    field_class = ContentTypeModelMultipleChoiceField


class UserModelMultipleChoiceField(django_filters.fields.ModelMultipleChoiceField):
    """
    Custom ModelMultipleChoiceField for user models, to show the result of
    get_user_display_name as the label rather than the default string representation
    """

    def label_from_instance(self, obj):
        return get_user_display_name(obj)


class MultipleUserFilter(django_filters.ModelMultipleChoiceFilter):
    field_class = UserModelMultipleChoiceField


class CollectionChoiceIterator(django_filters.fields.ModelChoiceIterator):
    @cached_property
    def min_depth(self):
        return self.queryset.get_min_depth()

    def choice(self, obj):
        return (obj.pk, obj.get_indented_name(self.min_depth, html=True))


class CollectionChoiceField(django_filters.fields.ModelChoiceField):
    iterator = CollectionChoiceIterator


class CollectionFilter(django_filters.ModelChoiceFilter):
    field_class = CollectionChoiceField


class RelatedFilterMixin:
    # Workaround for https://github.com/wagtail/wagtail/issues/6616 by changing
    # a filter on a related field into a filter on the primary key of instances
    # that match the filter value.

    def __init__(self, *args, use_subquery=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_subquery = use_subquery

    def filter(self, qs, value):
        filtered = super().filter(qs, value)
        if not self.use_subquery or not value:
            return filtered
        pks = list(filtered.values_list("pk", flat=True))
        return qs.filter(pk__in=pks)


class PopularTagsFilter(RelatedFilterMixin, django_filters.MultipleChoiceFilter):
    # This uses a MultipleChoiceFilter instead of a ModelMultipleChoiceFilter
    # because the queryset has been sliced, which means ModelMultipleChoiceFilter
    # cannot do further queries to validate the selected tags.
    pass


class BaseMediaFilterSet(WagtailFilterSet):
    permission_policy = None

    def __init__(
        self, data=None, queryset=None, *, request=None, prefix=None, is_searching=None
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        collections_qs = self.permission_policy.collections_user_has_any_permission_for(
            request.user, ["add", "change"]
        )
        # Add collection filter only if there are multiple collections
        if collections_qs.count() > 1:
            self.filters["collection_id"] = CollectionFilter(
                field_name="collection_id",
                label=_("Collection"),
                queryset=collections_qs,
            )

        popular_tags = popular_tags_for_model(self._meta.model)

        if popular_tags:
            self.filters["tag"] = PopularTagsFilter(
                label=_("Tag"),
                field_name="tags__name",
                choices=[(tag.name, tag.name) for tag in popular_tags],
                widget=forms.CheckboxSelectMultiple,
                use_subquery=is_searching,
                help_text=_("Filter by up to ten most popular tags."),
            )
