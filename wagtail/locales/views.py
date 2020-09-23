import functools

from django.db import transaction
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.edit_handlers import ObjectList, extract_panel_definitions_from_model_class
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.core.models import Locale
from wagtail.core.permissions import locale_permission_policy

from .components import get_locale_components
from .forms import LocaleForm
from .utils import get_locale_usage


@functools.lru_cache()
def get_locale_component_edit_handler(model):
    if hasattr(model, "edit_handler"):
        # use the edit handler specified on the class
        return model.edit_handler
    else:
        panels = extract_panel_definitions_from_model_class(model, exclude=["locale"])
        return ObjectList(panels)


class ComponentManager:
    def __init__(self, components):
        self.components = components

    @classmethod
    def from_request(cls, request, instance=None):
        components = []

        for component_model in get_locale_components():
            component_instance = component_model.objects.filter(locale=instance).first()
            edit_handler = get_locale_component_edit_handler(component_model).bind_to(
                model=component_model, instance=component_instance, request=request
            )
            form_class = edit_handler.get_form_class()
            prefix = "component_{}_{}".format(
                component_model._meta.app_label, component_model.__name__
            )

            if request.method == "POST":
                form = form_class(
                    request.POST,
                    request.FILES,
                    instance=component_instance,
                    prefix=prefix,
                )
            else:
                form = form_class(instance=component_instance, prefix=prefix)

            components.append((component_model, component_instance, form))

        return cls(components)

    def is_valid(self):
        return all(
            component_form.is_valid()
            for component_model, component_instance, component_form in self.components
        )

    def save(self, locale):
        for component_model, component_instance, component_form in self.components:
            component_instance = component_form.save(commit=False)
            component_instance.locale = locale
            component_instance.save()

    def __iter__(self):
        return iter(self.components)


class IndexView(generic.IndexView):
    template_name = 'wagtaillocales/index.html'
    page_title = gettext_lazy("Locales")
    add_item_label = gettext_lazy("Add a locale")
    context_object_name = 'locales'
    queryset = Locale.all_objects.all()

    def get_context_data(self):
        context = super().get_context_data()

        for locale in context['locales']:
            locale.num_pages, locale.num_others = get_locale_usage(locale)

        return context


class CreateView(generic.CreateView):
    page_title = gettext_lazy("Add locale")
    success_message = gettext_lazy("Locale '{0}' created.")
    template_name = 'wagtaillocales/create.html'

    def get_components(self):
        return ComponentManager.from_request(self.request)

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        self.components = ComponentManager.from_request(self.request)

        if form.is_valid() and self.get_components().is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        self.get_components().save(self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["components"] = self.get_components()
        return context


class EditView(generic.EditView):
    success_message = gettext_lazy("Locale '{0}' updated.")
    error_message = gettext_lazy("The locale could not be saved due to errors.")
    delete_item_label = gettext_lazy("Delete locale")
    context_object_name = 'locale'
    template_name = 'wagtaillocales/edit.html'
    queryset = Locale.all_objects.all()

    def get_components(self):
        return ComponentManager.from_request(self.request, instance=self.object)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid() and self.get_components().is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        self.get_components().save(self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["components"] = self.get_components()
        return context


class DeleteView(generic.DeleteView):
    success_message = gettext_lazy("Locale '{0}' deleted.")
    cannot_delete_message = gettext_lazy("This locale cannot be deleted because there are pages and/or other objects using it.")
    page_title = gettext_lazy("Delete locale")
    confirmation_message = gettext_lazy("Are you sure you want to delete this locale?")
    template_name = 'wagtaillocales/confirm_delete.html'
    queryset = Locale.all_objects.all()

    def can_delete(self, locale):
        return get_locale_usage(locale) == (0, 0)

    def get_context_data(self, object=None):
        context = context = super().get_context_data()
        context['can_delete'] = self.can_delete(object)
        return context

    def delete(self, request, *args, **kwargs):
        if self.can_delete(self.get_object()):
            return super().delete(request, *args, **kwargs)
        else:
            messages.error(request, self.cannot_delete_message)
            return super().get(request)


class LocaleViewSet(ModelViewSet):
    icon = 'site'
    model = Locale
    permission_policy = locale_permission_policy

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    def get_form_class(self, for_update=False):
        return LocaleForm
