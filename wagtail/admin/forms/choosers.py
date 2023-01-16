from django import forms
from django.core import validators
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from wagtail.models import Locale
from wagtail.search.backends import get_search_backend


class URLOrAbsolutePathValidator(validators.URLValidator):
    @staticmethod
    def is_absolute_path(value):
        return value.startswith("/")

    def __call__(self, value):
        if URLOrAbsolutePathValidator.is_absolute_path(value):
            return None
        else:
            return super().__call__(value)


class URLOrAbsolutePathField(forms.URLField):
    widget = TextInput
    default_validators = [URLOrAbsolutePathValidator()]

    def to_python(self, value):
        if not URLOrAbsolutePathValidator.is_absolute_path(value):
            value = super().to_python(value)
        return value


class ExternalLinkChooserForm(forms.Form):
    url = URLOrAbsolutePathField(required=True, label=_("URL"))
    link_text = forms.CharField(required=False)


class AnchorLinkChooserForm(forms.Form):
    url = forms.CharField(required=True, label="#")
    link_text = forms.CharField(required=False)


class EmailLinkChooserForm(forms.Form):
    email_address = forms.EmailField(required=True)
    link_text = forms.CharField(required=False)


class PhoneLinkChooserForm(forms.Form):
    phone_number = forms.CharField(required=True)
    link_text = forms.CharField(required=False)


class BaseFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_searching = False
        self.is_filtering_by_collection = False
        self.search_query = None

    def filter(self, objects):
        return objects


class SearchFilterMixin(forms.Form):
    """
    Mixin for a chooser listing filter form, to provide a search field
    """

    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search")}),
        required=False,
    )

    def filter(self, objects):
        objects = super().filter(objects)
        search_query = self.cleaned_data.get("q")
        if search_query:
            search_backend = get_search_backend()

            # The search should work as an autocomplete by preference, but only if
            # there are AutocompleteFields set up for this model in the search index;
            # if not, fall back on a standard search so that we get results at all
            if objects.model.get_autocomplete_search_fields():
                try:
                    objects = search_backend.autocomplete(search_query, objects)
                except NotImplementedError:
                    # Older search backends do not implement .autocomplete() but do support
                    # partial_match on .search(). Newer ones will ignore partial_match.
                    objects = search_backend.search(
                        search_query, objects, partial_match=True
                    )
            else:
                objects = search_backend.search(
                    search_query, objects, partial_match=True
                )

            self.is_searching = True
            self.search_query = search_query
        return objects


class CollectionFilterMixin(forms.Form):
    """
    Mixin for a chooser listing filter form, to provide a collection filter field.
    The view must pass a `collections` keyword argument when constructing the form
    """

    def __init__(self, *args, collections=None, **kwargs):
        super().__init__(*args, **kwargs)

        if collections:
            collection_choices = [
                ("", _("All collections"))
            ] + collections.get_indented_choices()
            self.fields["collection_id"] = forms.ChoiceField(
                label=_("Collection"),
                choices=collection_choices,
                required=False,
                widget=forms.Select(attrs={"data-chooser-modal-search-filter": True}),
            )

    def filter(self, objects):
        collection_id = self.cleaned_data.get("collection_id")
        if collection_id:
            self.is_filtering_by_collection = True
            objects = objects.filter(collection=collection_id)
        return super().filter(objects)


class LocaleFilterMixin(forms.Form):
    """
    Mixin for a chooser listing filter form, to provide a locale filter field.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locales = Locale.objects.all()
        if locales:
            self.fields["locale"] = forms.ChoiceField(
                choices=[
                    (locale.language_code, locale.get_display_name())
                    for locale in locales
                ],
                required=False,
                widget=forms.Select(attrs={"data-chooser-modal-search-filter": True}),
            )

    def filter(self, objects):
        selected_locale_code = self.cleaned_data.get("locale")
        if selected_locale_code:
            selected_locale = Locale.objects.get(language_code=selected_locale_code)
            objects = objects.filter(locale=selected_locale)
        return super().filter(objects)
