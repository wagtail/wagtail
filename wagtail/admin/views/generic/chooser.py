from django import forms
from django.contrib.admin.utils import unquote
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, View

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Table, TitleColumn
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed


class ModalPageFurnitureMixin(ContextMixin):
    """
    Add icon, page title and page subtitle to the template context
    """

    icon = None
    page_title = None
    page_subtitle = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "header_icon": self.icon,
                "page_title": self.page_title,
                "page_subtitle": self.page_subtitle,
            }
        )
        return context


class BaseChooseView(ModalPageFurnitureMixin, ContextMixin, View):
    model = None
    per_page = 10
    chosen_url_name = None
    results_url_name = None
    icon = "snippet"
    page_title = _("Choose")
    filter_form_class = None
    template_name = "wagtailadmin/generic/chooser/chooser.html"
    results_template_name = "wagtailadmin/generic/chooser/results.html"

    def get_object_list(self):
        return self.model.objects.all()

    def get_filter_form_class(self):
        if self.filter_form_class:
            return self.filter_form_class
        else:
            fields = {}
            if class_is_indexed(self.model):
                fields["q"] = forms.CharField(
                    label=_("Search term"), widget=forms.TextInput(), required=False
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
        search_query = form.cleaned_data.get("q")
        if search_query:
            search_backend = get_search_backend()
            objects = search_backend.search(search_query, objects)
            self.is_searching = True
            self.search_query = search_query
        return objects

    def get_results_url(self):
        return reverse(self.results_url_name)

    @property
    def columns(self):
        return [
            TitleColumn(
                "title",
                label=_("Title"),
                accessor=str,
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
        ]

    def get(self, request):
        objects = self.get_object_list()
        self.is_searching = False
        self.search_query = None

        self.filter_form = self.get_filter_form()
        if self.filter_form.is_valid():
            objects = self.filter_object_list(objects, self.filter_form)

        paginator = Paginator(objects, per_page=self.per_page)
        self.results = paginator.get_page(request.GET.get("p"))
        self.table = Table(self.columns, self.results)

        return self.render_to_response()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "results": self.results,
                "table": self.table,
                "results_url": self.get_results_url(),
                "is_searching": self.is_searching,
                "search_query": self.search_query,
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

    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            self.template_name,
            None,
            self.get_context_data(),
            json_data={
                "step": "choose",
            },
        )


class ChooseResultsView(BaseChooseView):
    def render_to_response(self):
        return TemplateResponse(
            self.request,
            self.results_template_name,
            self.get_context_data(),
        )


class ChosenView(View):
    model = None

    def get(self, request, pk):
        try:
            item = self.get_object(unquote(pk))
        except ObjectDoesNotExist:
            raise Http404

        return self.get_chosen_response(item)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    def get_object_id(self, instance):
        return instance.pk

    def get_display_title(self, instance):
        """
        Return a string representation of the given object instance
        """
        return str(instance)

    def get_edit_item_url(self, instance):
        return AdminURLFinder(user=self.request.user).get_edit_url(instance)

    def get_chosen_response_data(self, item):
        """
        Generate the result value to be returned when an object has been chosen
        """
        return {
            "id": str(self.get_object_id(item)),
            "title": self.get_display_title(item),
            "edit_link": self.get_edit_item_url(item),
        }

    def get_chosen_response(self, item):
        """
        Return the HTTP response to indicate that an object has been chosen
        """
        response_data = self.get_chosen_response_data(item)

        return render_modal_workflow(
            self.request,
            None,
            None,
            None,
            json_data={"step": "chosen", "result": response_data},
        )
