import re
import urllib.parse

from django.conf import settings
from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.core.paginator import InvalidPage, Paginator
from django.forms.models import modelform_factory
from django.http import Http404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, View

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.forms.choosers import (
    BaseFilterForm,
    CollectionFilterMixin,
    LocaleFilterMixin,
    SearchFilterMixin,
)
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Column, Table, TitleColumn
from wagtail.coreutils import resolve_model_string
from wagtail.models import CollectionMember, TranslatableMixin
from wagtail.permission_policies import BlanketPermissionPolicy, ModelPermissionPolicy
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


class ModelLookupMixin:
    """
    Allows a class to have a `model` attribute, which can be set as either a model class or a string,
    and then retrieve it as `model_class` to consistently get back a model class
    """

    model = None

    @cached_property
    def model_class(self):
        if self.model:
            return resolve_model_string(self.model)


class PreserveURLParametersMixin:
    """
    Adds support for passing designated URL parameters from the current request when constructing URLs
    for links / form actions.
    """

    preserve_url_parameters = ["multiple"]

    @cached_property
    def _preserved_param_string(self):
        params = {}
        for param in self.preserve_url_parameters:
            try:
                params[param] = self.request.GET[param]
            except KeyError:
                pass

        return urllib.parse.urlencode(params)

    def append_preserved_url_parameters(self, url):
        """
        Given a base URL (which might already include URL parameters), append any URL parameters
        from the preserve_url_parameters list that are present in the current request URL
        """
        if self._preserved_param_string:
            if "?" in url:
                url += "&" + self._preserved_param_string
            else:
                url += "?" + self._preserved_param_string

        return url


class CheckboxSelectColumn(Column):
    cell_template_name = "wagtailadmin/generic/chooser/checkbox_select_cell.html"


class BaseChooseView(
    ModalPageFurnitureMixin,
    ModelLookupMixin,
    PreserveURLParametersMixin,
    ContextMixin,
    View,
):
    """
    Provides common functionality for views that present a (possibly searchable / filterable) list
    of objects to choose from
    """

    per_page = 10
    ordering = None
    chosen_url_name = None
    chosen_multiple_url_name = None
    results_url_name = None
    icon = "snippet"
    page_title = _("Choose")
    filter_form_class = None
    template_name = "wagtailadmin/generic/chooser/chooser.html"
    results_template_name = "wagtailadmin/generic/chooser/results.html"
    construct_queryset_hook_name = None

    def get_object_list(self):
        return self.model_class.objects.all()

    def apply_object_list_ordering(self, objects):
        if isinstance(self.ordering, (list, tuple)):
            objects = objects.order_by(*self.ordering)
        elif self.ordering:
            objects = objects.order_by(self.ordering)
        elif objects.ordered:
            # Preserve the model-level ordering if specified
            pass
        else:
            # fall back on PK to ensure pagination is consistent
            objects = objects.order_by("pk")

        return objects

    def get_filter_form_class(self):
        if self.filter_form_class:
            return self.filter_form_class
        else:
            bases = [BaseFilterForm]
            if self.model_class:
                if class_is_indexed(self.model_class):
                    bases.insert(0, SearchFilterMixin)
                if issubclass(self.model_class, CollectionMember):
                    bases.insert(0, CollectionFilterMixin)

                i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
                if i18n_enabled and issubclass(self.model_class, TranslatableMixin):
                    bases.insert(0, LocaleFilterMixin)

            return type(
                "FilterForm",
                tuple(bases),
                {},
            )

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET)

    def filter_object_list(self, objects):
        if self.construct_queryset_hook_name:
            # allow hooks to modify the queryset
            for hook in hooks.get_hooks(self.construct_queryset_hook_name):
                objects = hook(objects, self.request)

        if self.filter_form.is_valid():
            objects = self.filter_form.filter(objects)
        return objects

    def get_results_url(self):
        return self.append_preserved_url_parameters(reverse(self.results_url_name))

    def get_chosen_multiple_url(self):
        return self.append_preserved_url_parameters(
            reverse(self.chosen_multiple_url_name)
        )

    @cached_property
    def is_multiple_choice(self):
        return self.request.GET.get("multiple")

    @property
    def columns(self):
        return [self.title_column]

    @property
    def title_column(self):
        if self.is_multiple_choice:
            return TitleColumn(
                "title",
                label=_("Title"),
                accessor=str,
                label_prefix="chooser-modal-select",
            )
        else:
            return TitleColumn(
                "title",
                label=_("Title"),
                accessor=str,
                get_url=(
                    lambda obj: self.append_preserved_url_parameters(
                        reverse(self.chosen_url_name, args=(quote(obj.pk),))
                    )
                ),
                link_attrs={"data-chooser-modal-choice": True},
            )

    @property
    def checkbox_column(self):
        return CheckboxSelectColumn(
            "select", label=_("Select"), width="1%", accessor="pk"
        )

    def get_results_page(self, request):
        objects = self.get_object_list()
        objects = self.apply_object_list_ordering(objects)
        objects = self.filter_object_list(objects)

        paginator = Paginator(objects, per_page=self.per_page)
        try:
            return paginator.page(request.GET.get("p", 1))
        except InvalidPage:
            raise Http404

    def get(self, request):
        self.filter_form = self.get_filter_form()
        self.results = self.get_results_page(request)

        columns = self.columns
        if self.is_multiple_choice:
            columns.insert(0, self.checkbox_column)
        self.table = Table(columns, self.results)

        return self.render_to_response()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        results_url = self.get_results_url()

        # For result pagination links, we need a version of results_url with parameters removed,
        # so that the pagination include can append its own parameters via the {% querystring %} template tag
        results_pagination_url = re.sub(r"\?.*$", "", results_url)

        context.update(
            {
                "results": self.results,
                "table": self.table,
                "results_url": results_url,
                "results_pagination_url": results_pagination_url,
                "is_searching": self.filter_form.is_searching,
                "is_filtering_by_collection": self.filter_form.is_filtering_by_collection,
                "is_multiple_choice": self.is_multiple_choice,
                "search_query": self.filter_form.search_query,
                "can_create": self.can_create(),
            }
        )
        if self.is_multiple_choice:
            context["chosen_multiple_url"] = self.get_chosen_multiple_url()
        return context

    def render_to_response(self):
        raise NotImplementedError()


class CreationFormMixin(ModelLookupMixin, PreserveURLParametersMixin):
    """
    Provides a form class for creating new objects
    """

    creation_form_class = None
    form_fields = None
    exclude_form_fields = None
    creation_form_template_name = "wagtailadmin/generic/chooser/creation_form.html"
    creation_tab_id = "create"
    create_action_label = _("Create")
    create_action_clicked_label = None
    create_url_name = None
    permission_policy = None

    def get_permission_policy(self):
        if self.permission_policy:
            return self.permission_policy
        elif self.model_class:
            return ModelPermissionPolicy(self.model_class)
        else:
            return BlanketPermissionPolicy(None)

    def can_create(self):
        return self.get_permission_policy().user_has_permission(
            self.request.user, "add"
        )

    def get_creation_form_class(self):
        if self.creation_form_class:
            return self.creation_form_class
        elif self.form_fields is not None or self.exclude_form_fields is not None:
            return modelform_factory(
                self.model_class,
                fields=self.form_fields,
                exclude=self.exclude_form_fields,
            )

    def get_creation_form_kwargs(self):
        kwargs = {}
        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_creation_form(self):
        form_class = self.get_creation_form_class()
        if not form_class:
            return None

        return form_class(**self.get_creation_form_kwargs())

    def get_create_url(self):
        if not self.create_url_name:
            raise ImproperlyConfigured(
                "%r must provide a create_url_name attribute or a get_create_url method"
                % type(self)
            )
        return self.append_preserved_url_parameters(reverse(self.create_url_name))

    def get_creation_form_context_data(self, form):
        return {
            "creation_form": form,
            "create_action_url": self.get_create_url(),
            "create_action_label": self.create_action_label,
            "create_action_clicked_label": self.create_action_clicked_label,
        }


class ChooseViewMixin:
    """
    A view that renders a complete modal response for the chooser, including a tab for the object
    listing and (optionally) a 'create' form
    """

    search_tab_label = _("Search")
    creation_tab_label = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "filter_form": self.filter_form,
                "search_tab_label": self.search_tab_label,
                "creation_tab_label": self.creation_tab_label
                or self.create_action_label,
            }
        )

        if context["can_create"]:
            creation_form = self.get_creation_form()
            if creation_form:
                context.update(self.get_creation_form_context_data(creation_form))

        return context

    def get_response_json_data(self):
        return {
            "step": "choose",
        }

    # Return the choose view as a ModalWorkflow response
    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            self.template_name,
            None,
            self.get_context_data(),
            json_data=self.get_response_json_data(),
        )


class ChooseView(ChooseViewMixin, CreationFormMixin, BaseChooseView):
    pass


class ChooseResultsViewMixin:
    """
    A view that renders just the object listing as an HTML fragment, used to replace the listing
    when paginating or searching
    """

    # Return just the HTML fragment for the results
    def render_to_response(self):
        return TemplateResponse(
            self.request,
            self.results_template_name,
            self.get_context_data(),
        )


class ChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BaseChooseView):
    pass


class ChosenResponseMixin:
    """
    Provides methods for returning the chosen object from the modal workflow.
    """

    response_data_title_key = "title"
    chosen_response_name = "chosen"

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
            self.response_data_title_key: self.get_display_title(item),
            "edit_url": self.get_edit_item_url(item),
        }

    def _wrap_chosen_response_data(self, response_data):
        """
        Wrap a response_data JSON payload in a modal workflow response
        """
        return render_modal_workflow(
            self.request,
            None,
            None,
            None,
            json_data={"step": self.chosen_response_name, "result": response_data},
        )

    def get_multiple_chosen_response(self, items):
        response_data = [self.get_chosen_response_data(item) for item in items]
        return self._wrap_chosen_response_data(response_data)

    def get_chosen_response(self, item):
        """
        Return the HTTP response to indicate that an object has been chosen
        """
        response_data = self.get_chosen_response_data(item)

        if self.request.GET.get("multiple"):
            # a multiple result was requested but we're only returning one,
            # so wrap as a list
            response_data = [response_data]

        return self._wrap_chosen_response_data(response_data)


class ChosenViewMixin(ModelLookupMixin):
    """
    A view that takes an object ID in the URL and returns a modal workflow response indicating
    that object has been chosen
    """

    def get_object(self, pk):
        return self.model_class.objects.get(pk=pk)

    def get(self, request, pk):
        try:
            item = self.get_object(unquote(pk))
        except ObjectDoesNotExist:
            raise Http404

        return self.get_chosen_response(item)


class ChosenView(ChosenViewMixin, ChosenResponseMixin, View):
    pass


class ChosenMultipleViewMixin(ModelLookupMixin):
    """
    A view that takes a list of 'id' URL parameters and returns a modal workflow response indicating
    that those objects have been chosen
    """

    def get_objects(self, pks):
        return self.model_class.objects.filter(pk__in=pks)

    def get(self, request):
        items = self.get_objects(request.GET.getlist("id"))
        return self.get_multiple_chosen_response(items)


class ChosenMultipleView(ChosenMultipleViewMixin, ChosenResponseMixin, View):
    pass


class CreateViewMixin:
    """
    A view that handles submissions of the 'create' form
    """

    model = None

    def dispatch(self, request, *args, **kwargs):
        if not self.can_create():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        self.form = self.get_creation_form()
        return self.get_reshow_creation_form_response()

    def save_form(self, form):
        return form.save()

    def post(self, request):
        self.form = self.get_creation_form()
        if self.form.is_valid():
            object = self.save_form(self.form)
            return self.get_chosen_response(object)
        else:
            return self.get_reshow_creation_form_response()

    def get_reshow_creation_form_response(self):
        context = {"view": self}
        context.update(self.get_creation_form_context_data(self.form))
        response_html = render_to_string(
            self.creation_form_template_name, context, self.request
        )
        return render_modal_workflow(
            self.request,
            None,
            None,
            None,
            json_data={
                "step": "reshow_creation_form",
                "htmlFragment": response_html,
            },
        )


class CreateView(CreateViewMixin, CreationFormMixin, ChosenResponseMixin, View):
    pass
