from django import forms
from django.contrib.admin.utils import quote
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.tables import TitleColumn
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenView,
)
from wagtail.models import Locale, TranslatableMixin
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed
from wagtail.snippets.views.snippets import get_snippet_model_from_url_params


class SnippetTitleColumn(TitleColumn):
    def __init__(self, name, model, **kwargs):
        self.model_opts = model._meta
        super().__init__(name, **kwargs)

    def get_value(self, instance):
        return str(instance)

    def get_link_url(self, instance, parent_context):
        return reverse(
            "wagtailsnippets:chosen",
            args=[
                self.model_opts.app_label,
                self.model_opts.model_name,
                quote(instance.pk),
            ],
        )


class BaseSnippetChooseView(BaseChooseView):
    filter_form_class = None
    icon = "snippet"
    page_title = _("Choose")
    template_name = "wagtailadmin/generic/chooser/chooser.html"
    results_template_name = "wagtailsnippets/chooser/results.html"
    per_page = 25

    @property
    def page_subtitle(self):
        return self.model._meta.verbose_name

    def get_filter_form_class(self):
        if self.filter_form_class:
            return self.filter_form_class
        else:
            fields = {}
            if class_is_indexed(self.model):
                placeholder = _("Search %(snippet_type_name)s") % {
                    "snippet_type_name": self.model._meta.verbose_name
                }
                fields["q"] = forms.CharField(
                    label=_("Search term"),
                    widget=forms.TextInput(attrs={"placeholder": placeholder}),
                    required=False,
                )

            if issubclass(self.model, TranslatableMixin):
                locales = Locale.objects.all()
                if locales:
                    fields["locale"] = forms.ChoiceField(
                        choices=[
                            (locale.language_code, locale.get_display_name())
                            for locale in locales
                        ],
                        required=False,
                        widget=forms.Select(
                            attrs={"data-chooser-modal-search-filter": True}
                        ),
                    )

            return type(
                "FilterForm",
                (forms.Form,),
                fields,
            )

    def filter_object_list(self, objects, form):
        selected_locale_code = form.cleaned_data.get("locale")
        if selected_locale_code:
            selected_locale = get_object_or_404(
                Locale, language_code=selected_locale_code
            )
            objects = objects.filter(locale=selected_locale)

        self.search_query = form.cleaned_data.get("q")
        if self.search_query:
            search_backend = get_search_backend()
            objects = search_backend.search(self.search_query, objects)
            self.is_searching = True

        return objects

    def get_results_url(self):
        return reverse(
            "wagtailsnippets:choose_results",
            args=(self.model._meta.app_label, self.model._meta.model_name),
        )

    @property
    def columns(self):
        return [
            SnippetTitleColumn(
                "title",
                self.model,
                label=_("Title"),
                link_attrs={"data-chooser-modal-choice": True},
            ),
        ]

    def get(self, request, app_label, model_name):
        self.model = get_snippet_model_from_url_params(app_label, model_name)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        context.update(
            {
                "snippet_type_name": self.model._meta.verbose_name,
                "add_url_name": f"wagtailsnippets_{app_label}_{model_name}:add",
            }
        )
        return context


class ChooseView(ChooseViewMixin, BaseSnippetChooseView):
    pass


class ChooseResultsView(ChooseResultsViewMixin, BaseSnippetChooseView):
    pass


class SnippetChosenView(ChosenView):
    response_data_title_key = "string"

    def get(self, request, *args, app_label, model_name, pk, **kwargs):
        self.model = get_snippet_model_from_url_params(app_label, model_name)
        return super().get(request, *args, pk, **kwargs)
