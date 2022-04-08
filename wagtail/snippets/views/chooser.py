from django.contrib.admin.utils import quote, unquote
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import View

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Table, TitleColumn
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


class BaseChooseView(View):
    def get(self, request, app_label, model_name):
        self.model = get_snippet_model_from_url_params(app_label, model_name)

        items = self.model.objects.all()

        # Preserve the snippet's model-level ordering if specified, but fall back on PK if not
        # (to ensure pagination is consistent)
        if not items.ordered:
            items = items.order_by("pk")

        # Filter by locale
        self.locale = None
        self.locale_filter = None
        self.selected_locale = None
        if issubclass(self.model, TranslatableMixin):
            # 'locale' is the Locale of the object that this snippet is being chosen for
            if request.GET.get("locale"):
                self.locale = get_object_or_404(
                    Locale, language_code=request.GET["locale"]
                )

            # 'locale_filter' is the current value of the "Locale" selector in the UI
            if request.GET.get("locale_filter"):
                self.locale_filter = get_object_or_404(
                    Locale, language_code=request.GET["locale_filter"]
                )

            self.selected_locale = self.locale_filter or self.locale

            if self.selected_locale:
                items = items.filter(locale=self.selected_locale)

        # Search
        self.is_searchable = class_is_indexed(self.model)
        self.is_searching = False
        self.search_query = None
        if self.is_searchable and "q" in request.GET:
            self.search_form = SearchForm(
                request.GET,
                placeholder=_("Search %(snippet_type_name)s")
                % {"snippet_type_name": self.model._meta.verbose_name},
            )

            if self.search_form.is_valid():
                self.search_query = self.search_form.cleaned_data["q"]

                search_backend = get_search_backend()
                items = search_backend.search(self.search_query, items)
                self.is_searching = True

        else:
            self.search_form = SearchForm(
                placeholder=_("Search %(snippet_type_name)s")
                % {"snippet_type_name": self.model._meta.verbose_name}
            )

        # Pagination
        paginator = Paginator(items, per_page=25)
        self.paginated_items = paginator.get_page(request.GET.get("p"))

        self.table = Table(
            [
                SnippetTitleColumn(
                    "title",
                    self.model,
                    label=_("Title"),
                    link_classname="snippet-choice",
                ),
            ],
            self.paginated_items,
        )

        return self.render_to_response()

    def render_to_response(self):
        raise NotImplementedError()


class ChooseView(BaseChooseView):
    # Return the choose view as a ModalWorkflow response
    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            "wagtailsnippets/chooser/choose.html",
            None,
            {
                "model_opts": self.model._meta,
                "items": self.paginated_items,
                "table": self.table,
                "is_searchable": self.is_searchable,
                "search_form": self.search_form,
                "query_string": self.search_query,
                "is_searching": self.is_searching,
                "locale": self.locale,
                "locale_filter": self.locale_filter,
                "selected_locale": self.selected_locale,
                "locale_options": Locale.objects.all()
                if issubclass(self.model, TranslatableMixin)
                else [],
            },
            json_data={"step": "choose"},
        )


class ChooseResultsView(BaseChooseView):
    # Return just the HTML fragment for the results
    def render_to_response(self):
        return TemplateResponse(
            self.request,
            "wagtailsnippets/chooser/results.html",
            {
                "model_opts": self.model._meta,
                "items": self.paginated_items,
                "table": self.table,
                "query_string": self.search_query,
                "is_searching": self.is_searching,
            },
        )


def chosen(request, app_label, model_name, pk):
    model = get_snippet_model_from_url_params(app_label, model_name)
    item = get_object_or_404(model, pk=unquote(pk))

    snippet_data = {
        "id": str(item.pk),
        "string": str(item),
        "edit_link": reverse(
            "wagtailsnippets:edit", args=(app_label, model_name, quote(item.pk))
        ),
    }

    return render_modal_workflow(
        request, None, None, None, json_data={"step": "chosen", "result": snippet_data}
    )
