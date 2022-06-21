from django import forms
from django.contrib.admin.utils import quote, unquote
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, View

from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Table, TitleColumn
from wagtail.admin.views.generic.chooser import ModalPageFurnitureMixin
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


class BaseChooseView(ModalPageFurnitureMixin, ContextMixin, View):
    filter_form_class = None
    icon = "snippet"
    page_title = _("Choose")
    template_name = "wagtailadmin/generic/chooser/chooser.html"
    results_template_name = "wagtailsnippets/chooser/results.html"
    per_page = 25

    @property
    def page_subtitle(self):
        return self.model._meta.verbose_name

    def get_object_list(self):
        objects = self.model.objects.all()

        # Preserve the snippet's model-level ordering if specified, but fall back on PK if not
        # (to ensure pagination is consistent)
        if not objects.ordered:
            objects = objects.order_by("pk")

        return objects

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

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET)

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

        objects = self.get_object_list()

        # Search
        self.is_searchable = class_is_indexed(self.model)
        self.is_searching = False
        self.search_query = None

        self.filter_form = self.get_filter_form()
        if self.filter_form.is_valid():
            objects = self.filter_object_list(objects, self.filter_form)

        # Pagination
        paginator = Paginator(objects, per_page=self.per_page)
        self.results = paginator.get_page(request.GET.get("p"))

        self.table = Table(
            self.columns,
            self.results,
        )

        return self.render_to_response()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        context.update(
            {
                "snippet_type_name": self.model._meta.verbose_name,
                "results": self.results,
                "table": self.table,
                "results_url": self.get_results_url(),
                "query_string": self.search_query,
                "is_searching": self.is_searching,
                "add_url_name": f"wagtailsnippets_{app_label}_{model_name}:add",
            }
        )
        return context

    def render_to_response(self):
        raise NotImplementedError()


class ChooseView(BaseChooseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context

    # Return the choose view as a ModalWorkflow response
    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            self.template_name,
            None,
            self.get_context_data(),
            json_data={"step": "choose"},
        )


class ChooseResultsView(BaseChooseView):
    # Return just the HTML fragment for the results
    def render_to_response(self):
        return TemplateResponse(
            self.request,
            self.results_template_name,
            self.get_context_data(),
        )


class ChosenView(View):
    def get(request, *args, app_label, model_name, pk, **kwargs):
        model = get_snippet_model_from_url_params(app_label, model_name)
        item = get_object_or_404(model, pk=unquote(pk))

        snippet_data = {
            "id": str(item.pk),
            "string": str(item),
            "edit_link": reverse(
                f"wagtailsnippets_{app_label}_{model_name}:edit", args=[quote(item.pk)]
            ),
        }

        return render_modal_workflow(
            request,
            None,
            None,
            None,
            json_data={"step": "chosen", "result": snippet_data},
        )
